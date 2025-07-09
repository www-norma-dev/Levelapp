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

class RelativeDateOption(str, Enum):
    """Enum representing the relative date options."""
    TODAY_PLUS_7 = "today plus 7"
    IN_1_MONTH = "in 1 month"
    IN_2_MONTHS = "in 2 months"
    IN_3_MONTHS = "in 3 months"
    IN_4_MONTHS = "in 4 months"
    TODAY = "today"
    TOMORROW = "tomorrow" 