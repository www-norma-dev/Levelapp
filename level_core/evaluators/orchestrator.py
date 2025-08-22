"""
Orchestrator service - complete production implementation.
Handles verify → init → launch flow with idempotency, rate limiting, and JWT tokens.
"""
import os
import hashlib
import json
import jwt
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from collections import defaultdict
from uuid import uuid4
import asyncio

from .orchestration_schemas import (
    WorkflowSession, LaunchResponse, VerificationResult, 
    CheckResult, ErrorCode
)
from .verifier import PrerequisiteVerifier


class OrchestratorService:
    def __init__(self, evaluation_service=None, logger=None):
        self.evaluation_service = evaluation_service
        self.logger = logger or self._get_default_logger()
        self.verifier = PrerequisiteVerifier()
        
        # In-memory session store with TTL
        self.sessions: Dict[str, WorkflowSession] = {}
        
        # Rate limiting: project_id -> request timestamps  
        self.rate_limiter: Dict[str, list] = defaultdict(list)
        self.max_requests_per_minute = int(os.getenv("ORCH_RATE_LIMIT_PER_MIN", "10"))
        
        # Session TTL from env
        self.session_ttl_minutes = int(os.getenv("ORCH_SESSION_TTL_MIN", "15"))
        
        # JWT secret from env
        self.jwt_secret = os.getenv("ORCHESTRATOR_JWT_SECRET", "dev-secret-change-in-production")
        
        # Start cleanup task
        self._start_cleanup_task()
    
    def _get_default_logger(self):
        """Fallback logger"""
        import logging
        return logging.getLogger(__name__)
    
    def _start_cleanup_task(self):
        """Start background session cleanup"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self._cleanup_expired_sessions())
            else:
                self.logger.info("No running event loop, session cleanup disabled")
        except RuntimeError:
            # No event loop, cleanup will be manual
            self.logger.info("No event loop available, session cleanup disabled")
    
    def _generate_seed_hash(self, seed: Dict[str, Any]) -> str:
        """Generate deterministic hash for idempotency"""
        seed_str = json.dumps(seed, sort_keys=True)
        return hashlib.sha256(seed_str.encode()).hexdigest()[:16]
    
    def _check_rate_limit(self, project_id: str) -> bool:
        """Rate limiting: 10 requests/min/project"""
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        
        # Clean old requests
        self.rate_limiter[project_id] = [
            ts for ts in self.rate_limiter[project_id] 
            if ts > minute_ago
        ]
        
        # Check limit
        if len(self.rate_limiter[project_id]) >= self.max_requests_per_minute:
            return False
        
        # Add current request
        self.rate_limiter[project_id].append(now)
        return True
    
    def _find_existing_session(self, project_id: str, workflow_type: str, seed_hash: str) -> Optional[WorkflowSession]:
        """Find existing session for idempotency"""
        for session in self.sessions.values():
            if (session.project_id == project_id and 
                session.workflow_type == workflow_type and 
                session.seed_hash == seed_hash and
                session.expires_at > datetime.now()):
                return session
        return None
    
    def _generate_launch_token(self, session_id, project_id: str, workflow_type: str) -> str:
        """Generate signed JWT launch token"""
        now = datetime.utcnow()
        payload = {
            "session_id": str(session_id),
            "project_id": project_id,
            "workflow_type": workflow_type,
            "exp": now + timedelta(minutes=5),
            "nbf": now,
            "aud": "levelapp-orchestrator"
        }
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")
    
    def _get_redirect_path(self, workflow_type: str, session_id) -> str:
        """Get redirect path for workflow type"""
        paths = {
            "generation": f"/dashboard/projects/{{project_id}}/evaluate?session_id={session_id}",
            "rag": f"/dashboard/projects/{{project_id}}/rag-workflow?session_id={session_id}",
            "extraction": f"/dashboard/projects/{{project_id}}/extraction-workflow?session_id={session_id}"
        }
        return paths.get(workflow_type, "/dashboard/projects/{project_id}")
    
    async def prepare_workflow(self, project_id: str, workflow_type: str, seed: Dict[str, Any]) -> LaunchResponse:
        """Main orchestration: verify → init → launch"""
        start_time = datetime.now()
        
        try:
            self.logger.info("orch.prepare.started", extra={
                "project_id": project_id, "workflow_type": workflow_type
            })
            
            # Rate limiting
            if not self._check_rate_limit(project_id):
                return LaunchResponse(
                    success=False,
                    verification=VerificationResult(
                        ready=False,
                        checks=[CheckResult(name="rate_limit", status="fail", detail="Too many requests")],
                        reasons=["Rate limit exceeded"],
                        codes=[ErrorCode.RATE_LIMITED]
                    )
                )
            
            # Idempotency check
            seed_hash = self._generate_seed_hash(seed)
            existing_session = self._find_existing_session(project_id, workflow_type, seed_hash)
            
            if existing_session:
                launch_token = self._generate_launch_token(existing_session.session_id, project_id, workflow_type)
                redirect_path = self._get_redirect_path(workflow_type, existing_session.session_id)
                
                self.logger.info("orch.prepare.idempotent", extra={
                    "project_id": project_id, "session_id": str(existing_session.session_id)
                })
                
                return LaunchResponse(
                    success=True,
                    session_id=existing_session.session_id,
                    launch_token=launch_token,
                    redirect_path=redirect_path.format(project_id=project_id)
                )
            
            # BLOCK 1: VERIFIER
            self.logger.info("orch.verify.started", extra={"project_id": project_id, "workflow_type": workflow_type})
            verification = await self.verifier.verify_workflow(project_id, workflow_type, seed)
            self.logger.info("orch.verify.finished", extra={
                "project_id": project_id, "workflow_type": workflow_type,
                "ready": verification.ready, "codes": [c.value for c in verification.codes]
            })
            
            if not verification.ready:
                return LaunchResponse(success=False, verification=verification)
            
            # BLOCK 2: INIT
            self.logger.info("orch.init.started", extra={"project_id": project_id, "workflow_type": workflow_type})
            session = await self._initialize_workflow(project_id, workflow_type, seed, seed_hash)
            self.logger.info("orch.init.finished", extra={
                "project_id": project_id, "workflow_type": workflow_type, "session_id": str(session.session_id)
            })
            
            # BLOCK 3: LAUNCH
            launch_token = self._generate_launch_token(session.session_id, project_id, workflow_type)
            redirect_path = self._get_redirect_path(workflow_type, session.session_id)
            
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            self.logger.info("orch.launch.granted", extra={
                "project_id": project_id, "workflow_type": workflow_type,
                "session_id": str(session.session_id), "duration_ms": duration_ms
            })
            
            return LaunchResponse(
                success=True,
                session_id=session.session_id,
                launch_token=launch_token,
                redirect_path=redirect_path.format(project_id=project_id)
            )
            
        except Exception as e:
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            self.logger.error("orch.prepare.error", extra={
                "project_id": project_id, "workflow_type": workflow_type,
                "error": str(e), "duration_ms": duration_ms
            })
            
            return LaunchResponse(
                success=False,
                verification=VerificationResult(
                    ready=False,
                    checks=[CheckResult(name="system", status="fail", detail=str(e))],
                    reasons=[f"System error: {str(e)}"],
                    codes=[ErrorCode.SYSTEM_ERROR]
                )
            )
    
    async def _initialize_workflow(self, project_id: str, workflow_type: str, seed: Dict[str, Any], seed_hash: str) -> WorkflowSession:
        """Light initialization - no heavy lifting"""
        context = {}
        
        if workflow_type == "generation":
            context = {
                "endpoint_url": seed.get("endpoint"),
                "available_models": ["meta-llama/Llama-3.3-70B-Instruct", "meta-llama/Meta-Llama-3.1-8B-Instruct"]
            }
        elif workflow_type == "rag":
            context = {
                "source_url": seed.get("source_url"),
                "chunk_size": seed.get("chunk_size", 512)
            }
        elif workflow_type == "extraction":
            context = {
                "document_ids": seed.get("document_ids", []),
                "schema_id": seed.get("schema_id")
            }
        
        session = WorkflowSession(
            session_id=uuid4(),
            project_id=project_id,
            workflow_type=workflow_type,
            seed_hash=seed_hash,
            context=context,
            status="ready",
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(minutes=self.session_ttl_minutes)
        )
        
        # Store session
        self.sessions[str(session.session_id)] = session
        return session
    
    async def _cleanup_expired_sessions(self):
        """Background task to cleanup expired sessions"""
        while True:
            try:
                now = datetime.now()
                expired_sessions = [
                    session_id for session_id, session in self.sessions.items()
                    if session.expires_at <= now
                ]
                
                for session_id in expired_sessions:
                    del self.sessions[session_id]
                    
                if expired_sessions:
                    self.logger.info("orch.cleanup.completed", extra={"cleaned_sessions": len(expired_sessions)})
                    
            except Exception as e:
                self.logger.error("orch.cleanup.error", extra={"error": str(e)})
            
            await asyncio.sleep(300)  # 5 minutes
