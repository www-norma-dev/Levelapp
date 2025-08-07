from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class LiteLLMConfig(BaseModel):
    """
    Generic config for any LLM provider.
    """
    provider: str = "openai"           # e.g. 'openai', 'ionos', 'custom'
    model: str = "gpt-4o-mini"
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    additional_config: Dict[str, Any] = Field(default_factory=lambda: {
        "temperature": 0.0,
        "max_tokens": 150
    })

class EvaluationResult(BaseModel):
    match_level: float = Field(0.0, description="Matching score (0=no match)")
    justification: str = Field("", description="Evaluator explanation")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
