"""levelapp/entities/metric.py"""
from typing import Callable, Any, List

from pydantic import BaseModel, Field


class Metric(BaseModel):
    """Represents a metric for evaluation"""
    name: str
    compute: Callable[[Any, Any], float]
    description: str = ""


class RAGMetrics(BaseModel):
    """Computed NLP metrics for RAG evaluation"""
    bleu_score: float
    rouge_l_f1: float
    meteor_score: float
    bertscore_f1: float


class LLMComparison(BaseModel):
    """LLM-as-judge comparison result"""
    better_answer: str  # 'expected', 'chatbot', or 'tie'
    justification: str
    missing_facts: List[str] = Field(default_factory=list)
