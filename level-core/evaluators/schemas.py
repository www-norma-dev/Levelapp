"""
'evaluators/schemas.py': Schema definitions for evaluator configuration and evaluation results.
"""
from typing import Union, Dict, Optional, Any
from pydantic import BaseModel, Field, ConfigDict


class EvaluationConfig(BaseModel):

    model_config = ConfigDict(protected_namespaces=())

    """Configuration model for setting up an evaluator instance."""

    api_url: Union[str, None] = None
    api_key: Union[str, None] = None
    model_id: Union[str, None] = None
    llm_config: Dict = {
        "top-k": 5,
        "top-p": 0.9,
        "temperature": 0.0,
        "max_tokens": 150,
    }


class EvaluationResult(BaseModel):
    """
    Output structure for an evaluation result."""
    match_level: int = Field(0, description="0 if parsing/validation failed")
    justification: str = Field("", description="Reason for low rating")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
