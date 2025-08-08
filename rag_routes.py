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

# Removed debug printing of API keys for logging hygiene

from level_core.simluators.rag_schemas import (
    RAGInitRequest, RAGInitResponse, ChunkSelectionRequest,
    ExpectedAnswerResponse, RAGEvaluationRequest, RAGEvaluationResult
)
from level_core.simluators.rag_simulator import RAGSimulator
from level_core.evaluators.service import EvaluationService
from level_core.generators.service import GenerationService, GenerationConfig
from level_core.evaluators.schemas import EvaluationConfig
from level_core.simluators.event_collector import log_rag_event

# Initialize router
rag_router = APIRouter(prefix="/rag", tags=["RAG Evaluation"])

# Global session storage and singleton simulator
_GLOBAL_SESSIONS: Dict[str, Dict[str, Any]] = defaultdict(dict)
_SINGLETON_SIMULATOR = None

# Configuration from environment
def get_config():
    """Get default configuration from environment variables.

    Note: The /rag/init endpoint requires a chatbot_base_url in the request.
    These env values act as developer defaults and are used only when explicitly
    passed through by the client or for local tooling.
    """
    config = {
        # Default base URL for chatbot (no trailing slash). Can be overridden by request.
        "chatbot_base_url": os.getenv("CHATBOT_BASE_URL", os.getenv("CHATBOT_ENDPOINT", "http://localhost:8000")),
        # Default path for chat endpoint (leading slash). Can be overridden by request.
        "chatbot_chat_path": os.getenv("CHATBOT_CHAT_PATH", "/"),
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        "ionos_api_key": os.getenv("IONOS_API_KEY")
    }
    # Avoid logging API keys or prefixes to prevent leakage
    return config

def get_evaluation_service(config: Dict[str, str] = Depends(get_config)):
    """Get evaluation service instance with provider configs."""
    from logging import Logger
    svc = EvaluationService(logger=Logger("RAGEvaluation"))
    # Configure OpenAI if key present
    if config.get("openai_api_key"):
        svc.set_config("openai", EvaluationConfig(api_key=config["openai_api_key"], model_id="gpt-4o-mini"))
    # Configure IONOS if key present
    if config.get("ionos_api_key"):
        svc.set_config("ionos", EvaluationConfig(api_key=config["ionos_api_key"], api_url=os.getenv("IONOS_API_URL", "https://api.ionos.ai"), model_id=os.getenv("IONOS_MODEL_ID", "")))
    return svc

def get_generation_service(config: Dict[str, str] = Depends(get_config)):
    """Get generation service instance with provider configs."""
    from logging import Logger
    gsvc = GenerationService(logger=Logger("RAGGeneration"))
    if config.get("openai_api_key"):
        gsvc.set_config("openai", GenerationConfig(api_key=config["openai_api_key"], model_id=os.getenv("LEVELAPP_EXPECTED_MODEL", "gpt-4o-mini")))
    return gsvc

def get_rag_simulator(config: Dict[str, str] = Depends(get_config), 
                     evaluation_service: EvaluationService = Depends(get_evaluation_service),
                     generation_service: GenerationService = Depends(get_generation_service)) -> RAGSimulator:
    """Get singleton RAG simulator instance."""
    global _SINGLETON_SIMULATOR
    
    if _SINGLETON_SIMULATOR is None:
        headers = {"Content-Type": "application/json"}
        _SINGLETON_SIMULATOR = RAGSimulator(
            evaluation_service,
            generation_service,
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