from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID, uuid4
from enum import Enum

class RAGInitRequest(BaseModel):
    """Request to initialize RAG system and scrape page"""
    # Allow field names like `model_id` that would otherwise conflict with `model_` namespace
    model_config = ConfigDict(protected_namespaces=())
    page_url: str = Field(..., description="URL to scrape and index")
    model_id: str = Field(default="meta-llama/Llama-3.3-70B-Instruct", description="Model ID for headers")
    chunk_size: int = Field(default=500, description="Chunk size to match chatbot's chunker")

class ChunkInfo(BaseModel):
    """Represents a single chunk with metadata"""
    index: int = Field(..., description="Chunk index")
    content: str = Field(..., description="Chunk text content")
    word_count: int = Field(..., description="Number of words in chunk")

class RAGInitResponse(BaseModel):
    """Combined response with initialization status and scraped chunks"""
    session_id: UUID = Field(default_factory=uuid4, description="Unique session ID")
    page_url: str = Field(..., description="Scraped page URL")
    initialization_status: str = Field(..., description="RAG initialization status")
    total_chunks: int = Field(..., description="Total number of chunks")
    chunks: List[ChunkInfo] = Field(..., description="List of chunks with indices")
    chunk_size: int = Field(..., description="Character size per chunk")

class ChunkSelectionRequest(BaseModel):
    """Human-selected chunks for expected answer generation"""
    model_config = ConfigDict(protected_namespaces=())
    session_id: UUID = Field(..., description="Session ID from initialization")
    prompt: str = Field(..., description="User's original question")
    manual_order: List[int] = Field(..., description="Human-selected chunk indices")
    model_id: str = Field(default="meta-llama/Llama-3.3-70B-Instruct", description="Model ID")

class ExpectedAnswerResponse(BaseModel):
    """Generated expected answer with option for human editing"""
    session_id: UUID = Field(..., description="Session ID")
    prompt: str = Field(..., description="Original question")
    generated_answer: str = Field(..., description="AI-generated expected answer")
    selected_chunks: List[str] = Field(..., description="Ordered chunk contents used")

class RAGEvaluationRequest(BaseModel):
    """Complete RAG evaluation request"""
    model_config = ConfigDict(protected_namespaces=())
    session_id: UUID = Field(..., description="Session ID from initialization")
    prompt: str = Field(..., description="User question")
    expected_answer: str = Field(..., description="Human-confirmed expected answer")
    model_id: str = Field(default="meta-llama/Llama-3.3-70B-Instruct", description="Model ID")

class RAGMetrics(BaseModel):
    """Computed NLP metrics for RAG evaluation"""
    bleu_score: float = Field(..., description="BLEU score (0-1)")
    rouge_l_f1: float = Field(..., description="ROUGE-L F1 score (0-1)")
    meteor_score: float = Field(..., description="METEOR score (0-1)")
    bertscore_precision: float = Field(..., description="BERTScore precision")
    bertscore_recall: float = Field(..., description="BERTScore recall")
    bertscore_f1: float = Field(..., description="BERTScore F1")

class LLMComparison(BaseModel):
    """LLM-as-judge comparison result"""
    better_answer: str = Field(..., description="'expected', 'chatbot', or 'tie'")
    justification: str = Field(..., description="Detailed explanation with missing facts")
    missing_facts: List[str] = Field(default_factory=list, description="List of missing factual statements")

class RAGEvaluationResult(BaseModel):
    """Complete RAG evaluation result"""
    evaluation_id: UUID = Field(default_factory=uuid4, description="Unique evaluation ID")
    session_id: UUID = Field(..., description="Session ID")
    page_url: str = Field(..., description="Evaluated page URL")
    prompt: str = Field(..., description="Original question")
    expected_answer: str = Field(..., description="Human-curated expected answer")
    chatbot_answer: str = Field(..., description="Actual chatbot response")
    metrics: RAGMetrics = Field(..., description="NLP metrics")
    llm_comparison: LLMComparison = Field(..., description="LLM judgment")
    execution_time: float = Field(..., description="Total execution time in seconds")
    created_at: str = Field(..., description="ISO timestamp")