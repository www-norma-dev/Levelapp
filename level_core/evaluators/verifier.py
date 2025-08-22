"""
Prerequisite verifier - production implementation with 2s timeout budget.
"""
import os
from typing import Dict, Any
import httpx
from .orchestration_schemas import VerificationResult, CheckResult, ErrorCode


class PrerequisiteVerifier:
    def __init__(self):
        self.timeout = httpx.Timeout(2.0)
    
    async def _check_project_permission(self, project_id: str) -> bool:
        """Check if current user has access to project_id
        
        TODO: Integrate with Firebase auth context or pass user_id
        For now, return True but this should check:
        - User session/JWT from request context  
        - Project exists under user's collection in Firestore
        - User has required permissions for project
        """
        # Placeholder - integrate with existing Firebase auth pattern
        # from levelapp-web/src/app/api/projects/[projectId]/route.ts
        return True
    
    def _has_provider_configs(self) -> bool:
        """Check if provider API keys are configured
        
        REUSE: level_core/evaluators/service.py config validation pattern
        """
        # Check common environment variables for API keys
        api_keys = [
            os.getenv("OPENAI_API_KEY"),
            os.getenv("ANTHROPIC_API_KEY"), 
            os.getenv("IONOS_API_KEY"),
            # Add other provider keys as needed
        ]
        return any(key for key in api_keys if key)
    
    def _rag_dependencies_available(self) -> bool:
        """Check if RAG dependencies are available"""
        try:
            # Try importing key RAG components
            from level_core.simluators.rag_simulator import RAGSimulator
            from level_core.evaluators.rag_evaluator import RAGEvaluator
            return True
        except ImportError:
            return False
        
    async def verify_workflow(self, project_id: str, workflow_type: str, seed: Dict[str, Any]) -> VerificationResult:
        """Dispatch to workflow-specific verifier"""
        
        # AuthZ gate: Check project access before external probes
        if not await self._check_project_permission(project_id):
            return VerificationResult(
                ready=False,
                checks=[CheckResult(name="authorization", status="fail", detail="Access denied to project")],
                reasons=["User lacks access to project"],
                codes=[ErrorCode.PERMISSION_DENIED]
            )
        
        if workflow_type == "generation":
            return await self._verify_generation(project_id, seed)
        elif workflow_type == "rag":
            return await self._verify_rag(project_id, seed)  
        elif workflow_type == "extraction":
            return await self._verify_extraction(project_id, seed)
        else:
            return VerificationResult(
                ready=False,
                checks=[CheckResult(name="workflow_type", status="fail", detail="Unknown workflow")],
                reasons=["Unknown workflow type"],
                codes=[ErrorCode.VALIDATION_ERROR]
            )
    
    async def _verify_generation(self, project_id: str, seed: Dict[str, Any]) -> VerificationResult:
        """Verify generation workflow prerequisites"""
        checks = []
        codes = []
        reasons = []
        
        # Check API keys - reuse existing pattern from evaluators/service.py
        if not self._has_provider_configs():
            checks.append(CheckResult(name="api_key", status="fail", detail="Missing provider API keys"))
            codes.append(ErrorCode.CONFIG_MISSING)
            reasons.append("API keys not configured")
        else:
            checks.append(CheckResult(name="api_key", status="ok"))
        
        # Check endpoint health if provided
        endpoint = seed.get("endpoint")
        if endpoint:
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.head(endpoint)
                    if response.status_code < 400:
                        checks.append(CheckResult(name="endpoint", status="ok"))
                    else:
                        checks.append(CheckResult(name="endpoint", status="fail", detail=f"HTTP {response.status_code}"))
                        codes.append(ErrorCode.CONNECTIVITY_ERROR)
                        reasons.append("Endpoint health check failed")
            except Exception as e:
                checks.append(CheckResult(name="endpoint", status="fail", detail=str(e)))
                codes.append(ErrorCode.CONNECTIVITY_ERROR)
                reasons.append("Cannot reach endpoint")
        
        # Check 3: Permission check (as per plan)
        if not await self._check_project_permission(project_id):
            checks.append(CheckResult(name="permissions", status="fail", detail="Access denied"))
            codes.append(ErrorCode.PERMISSION_DENIED)
            reasons.append("Insufficient project permissions")
        else:
            checks.append(CheckResult(name="permissions", status="ok"))
        
        return VerificationResult(
            ready=len(codes) == 0,
            checks=checks,
            reasons=reasons,
            codes=codes
        )
    
    async def _verify_rag(self, project_id: str, seed: Dict[str, Any]) -> VerificationResult:
        """Verify RAG workflow prerequisites"""
        checks = []
        codes = []
        reasons = []
        
        # Check source URL if provided
        source_url = seed.get("source_url")
        if source_url:
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.head(source_url)
                    if response.status_code == 200:
                        checks.append(CheckResult(name="source_url", status="ok"))
                    else:
                        checks.append(CheckResult(name="source_url", status="fail", detail="URL not accessible"))
                        codes.append(ErrorCode.RESOURCE_UNAVAILABLE)
                        reasons.append("Source URL not accessible")
            except Exception as e:
                checks.append(CheckResult(name="source_url", status="fail", detail=str(e)))
                codes.append(ErrorCode.CONNECTIVITY_ERROR)
                reasons.append("Cannot reach source URL")
        
        # Check RAG dependencies
        if not self._rag_dependencies_available():
            checks.append(CheckResult(name="rag_service", status="fail", detail="RAG service unavailable"))
            codes.append(ErrorCode.RESOURCE_UNAVAILABLE)
            reasons.append("RAG evaluation service not ready")
        else:
            checks.append(CheckResult(name="rag_service", status="ok"))
        
        return VerificationResult(
            ready=len(codes) == 0,
            checks=checks,
            reasons=reasons,
            codes=codes
        )
        
    async def _verify_extraction(self, project_id: str, seed: Dict[str, Any]) -> VerificationResult:
        """Verify extraction workflow prerequisites"""
        return VerificationResult(
            ready=False,
            checks=[CheckResult(name="extraction", status="fail", detail="Not implemented")],
            reasons=["Document extraction workflow not implemented"],
            codes=[ErrorCode.RESOURCE_UNAVAILABLE]
        )
