"""
levelapp_core_simulators/schemas.py: Generic Pydantic models for simulator data structures.
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel
from enum import Enum

class InteractionDetails(BaseModel):
    """Model representing details of a simulated interaction."""
    reply: Optional[str] = "No response"
    extracted_metadata: Optional[Dict[str, Any]] = {}
    handoff_details: Optional[Dict[str, Any]] = {}
    interaction_type: Optional[str] = ""

class InteractionEvaluationResult(BaseModel):
    """Model representing the evaluation result of an interaction."""
    evaluations: Dict[str, Any] 
    extracted_metadata_evaluation: float
    scenario_id: str

