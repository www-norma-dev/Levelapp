"""
'evaluators/schemas.py': Schema definitions for evaluator configuration and evaluation results.
"""

from typing import Union, Dict, Optional, Any
from pydantic import BaseModel, Field, ConfigDict


class EvaluationConfig(BaseModel):
    """Configuration model for setting up an evaluator instance."""

    model_config = ConfigDict(protected_namespaces=())  # Allows arbitrary field names

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
    Output structure for a generic evaluation result.

    Fields:
        match_level: Integer scale indicating evaluation score (0 = fail or no match).
        justification: Short explanation from the evaluator.
        metadata: Optional extra info (token count, cost, etc.)
    """
    match_level: int = Field(0, description="Matching score: 0 = no match / failure")
    justification: str = Field("", description="Evaluator justification or explanation")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    ## To be Added : Support multiple metrics in future as done in the reasarch (e.g., BLEU, ROUGE, etc.)
    ## and Why not extend this with: metrics: Dict[str, float] or an enum-based MetricResult
