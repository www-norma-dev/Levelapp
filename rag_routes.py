"""
RAG evaluation routes for human-in-the-loop workflow.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any
import os
from collections import defaultdict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Debug: Print what API key is loaded
api_key = os.getenv("OPENAI_API_KEY")
print(f"DEBUG: RAG Routes - API Key loaded: {api_key[:20]}..." if api_key else "DEBUG: RAG Routes - No API key found!")

from level_core.simluators.rag_schemas import (
    RAGInitRequest, RAGInitResponse, ChunkSelectionRequest,
    ExpectedAnswerResponse, RAGEvaluationRequest, RAGEvaluationResult
)
from level_core.simluators.rag_simulator import RAGSimulator
from level_core.evaluators.service import EvaluationService
from level_core.simluators.event_collector import log_rag_event

# Initialize router
rag_router = APIRouter(prefix="/rag", tags=["RAG Evaluation"])

# Global session storage and singleton simulator
_GLOBAL_SESSIONS: Dict[str, Dict[str, Any]] = defaultdict(dict)
_SINGLETON_SIMULATOR = None

# Configuration from environment
def get_config():
    """Get configuration from environment variables."""
    config = {
    # Base URL for chatbot (no trailing slash)
    "chatbot_base_url": os.getenv("CHATBOT_BASE_URL", os.getenv("CHATBOT_ENDPOINT", "http://localhost:8000")),
    # Path for chat endpoint (leading slash); default to root to match your chatbot
    "chatbot_chat_path": os.getenv("CHATBOT_CHAT_PATH", "/"),
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        "ionos_api_key": os.getenv("IONOS_API_KEY")
    }
    print(f"DEBUG: Config loaded - OpenAI key: {config['openai_api_key'][:20]}..." if config['openai_api_key'] else "DEBUG: Config - No OpenAI key!")
    return config

def get_evaluation_service():
    """Get evaluation service instance."""
    from logging import Logger
    return EvaluationService(logger=Logger("RAGEvaluation"))

def get_rag_simulator(config: Dict[str, str] = Depends(get_config), 
                     evaluation_service: EvaluationService = Depends(get_evaluation_service)) -> RAGSimulator:
    """Get singleton RAG simulator instance."""
    global _SINGLETON_SIMULATOR
    
    if _SINGLETON_SIMULATOR is None:
        headers = {"Content-Type": "application/json"}
        _SINGLETON_SIMULATOR = RAGSimulator(
            evaluation_service,
            endpoint_base=config["chatbot_base_url"].rstrip("/"),
            chat_path=config["chatbot_chat_path"] if config["chatbot_chat_path"].startswith("/") else f"/{config['chatbot_chat_path']}",
            headers=headers,
        )
        _SINGLETON_SIMULATOR.sessions = _GLOBAL_SESSIONS
        print(f"DEBUG: Created new singleton simulator with {len(_GLOBAL_SESSIONS)} sessions")
    else:
        print(f"DEBUG: Reusing singleton simulator with {len(_GLOBAL_SESSIONS)} sessions")
    
    return _SINGLETON_SIMULATOR


@rag_router.post("/init", response_model=RAGInitResponse)
async def initialize_rag_and_scrape(
    request: RAGInitRequest,
    simulator: RAGSimulator = Depends(get_rag_simulator)
):
    """
    Step 1: Initialize RAG system and scrape page in one call.
    """
    try:
        result = await simulator.initialize_rag_and_scrape(request)
        print(f"DEBUG: Session created: {result.session_id}")
        print(f"DEBUG: Total sessions after init: {len(_GLOBAL_SESSIONS)}")
        log_rag_event("INFO", f"RAG initialized and scraped for {request.page_url}")
        # Convert to dict to ensure proper JSON serialization
        return JSONResponse(content=result.model_dump(mode='json'), status_code=status.HTTP_200_OK)
    except Exception as e:
        log_rag_event("ERROR", f"RAG initialization failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAG initialization failed: {str(e)}"
        )

@rag_router.post("/generate-expected", response_model=ExpectedAnswerResponse)
async def generate_expected_answer(
    request: ChunkSelectionRequest,
    simulator: RAGSimulator = Depends(get_rag_simulator)
):
    """
    Step 2: Generate expected answer from human-selected chunks.
    """
    try:
        print(f"DEBUG: Looking for session: {request.session_id}")
        print(f"DEBUG: Available sessions: {list(_GLOBAL_SESSIONS.keys())}")
        result = await simulator.generate_expected_answer(request)
        log_rag_event("INFO", "Expected answer generated successfully")
        return JSONResponse(content=result.model_dump(mode='json'), status_code=status.HTTP_200_OK)
    except Exception as e:
        log_rag_event("ERROR", f"Expected answer generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Expected answer generation failed: {str(e)}"
        )

@rag_router.post("/evaluate", response_model=RAGEvaluationResult)
async def evaluate_rag_retrieval(
    request: RAGEvaluationRequest,
    simulator: RAGSimulator = Depends(get_rag_simulator)
):
    """
    Step 3: Complete RAG evaluation with automatic chatbot query.
    
    This endpoint performs the complete evaluation:
    1. Automatically queries the chatbot with the prompt
    2. Computes NLP metrics (BLEU, ROUGE-L, METEOR, BERTScore)
    3. Uses LLM-as-judge to compare expected vs actual answers
    4. Returns comprehensive evaluation results
    """
    try:
        result = await simulator.evaluate_rag_retrieval(request)
        log_rag_event("INFO", "RAG evaluation completed successfully")
        return JSONResponse(content=result.model_dump(mode='json'), status_code=status.HTTP_200_OK)
    except Exception as e:
        log_rag_event("ERROR", f"RAG evaluation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAG evaluation failed: {str(e)}"
        )

@rag_router.delete("/session/{session_id}")
async def cleanup_session(
    session_id: str,
    simulator: RAGSimulator = Depends(get_rag_simulator)
):
    """
    Clean up session data to free memory.
    
    Args:
        session_id: Session ID to clean up
    """
    try:
        from uuid import UUID
        session_uuid = UUID(session_id)
        success = simulator.cleanup_session(session_uuid)
        
        if success:
            return JSONResponse(
                content={"message": f"Session {session_id} cleaned up successfully"},
                status_code=status.HTTP_200_OK
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid session ID format: {session_id}"
        )
    except Exception as e:
        log_rag_event("ERROR", f"Session cleanup failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Session cleanup failed: {str(e)}"
        )