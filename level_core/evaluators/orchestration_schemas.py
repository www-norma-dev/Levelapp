"""
Orchestration schemas for workflow management - minimal production implementation.
"""
from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from typing import Literal


class ErrorCode(Enum):
    CONFIG_MISSING = "CONFIG_MISSING"
    RESOURCE_UNAVAILABLE = "RESOURCE_UNAVAILABLE"  
    CONNECTIVITY_ERROR = "CONNECTIVITY_ERROR"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    RATE_LIMITED = "RATE_LIMITED"
    SYSTEM_ERROR = "SYSTEM_ERROR"


class CheckResult(BaseModel):
    name: str
    status: Literal["ok", "fail", "warn"]
    detail: Optional[str] = None


class VerificationResult(BaseModel):
    ready: bool
    checks: List[CheckResult]
    reasons: List[str]
    codes: List[ErrorCode]


class WorkflowPrepareRequest(BaseModel):
    seed: Dict[str, Any]


class LaunchResponse(BaseModel):
    success: bool
    session_id: Optional[UUID] = None
    launch_token: Optional[str] = None
    redirect_path: Optional[str] = None
    verification: Optional[VerificationResult] = None


class WorkflowSession(BaseModel):
    session_id: UUID
    project_id: str
    workflow_type: str
    seed_hash: str
    context: Dict[str, Any]
    status: str
    created_at: datetime
    expires_at: datetime
