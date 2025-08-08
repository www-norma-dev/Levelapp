from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID, uuid4
from enum import Enum
from level_core.entities.metric import RAGMetrics, LLMComparison

class RAGInitRequest(BaseModel):
    """Request to initialize RAG system and scrape page"""
    # Allow field names like `model_id` that would otherwise conflict with `model_` namespace
    model_config = ConfigDict(protected_namespaces=())
    page_url: str = Field(..., description="URL to scrape and index")
    model_id: str = Field(default="meta-llama/Llama-3.3-70B-Instruct", description="Model ID for headers")
    chunk_size: int = Field(default=500, description="Chunk size to match chatbot's chunker")
    chatbot_base_url: str = Field(
        ...,
        description="Chatbot base URL (e.g., http://localhost:8000). Required to query the user's chatbot."
    )
    chatbot_chat_path: Optional[str] = Field(
        default=None,
        description="Optional chatbot chat path (e.g., / or /chat). Overrides environment if provided."
    )

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
    expected_model: Optional[str] = Field(default=None, description="LLM to generate the expected (golden) answer")

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

## RAGMetrics and LLMComparison now defined in entities.metric and imported above

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