"""
RAG-specific simulator for human-in-the-loop retrieval evaluation.
"""
import asyncio
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
import textwrap
from uuid import uuid4, UUID

from .rag_schemas import (
    RAGInitRequest, RAGInitResponse, ChunkSelectionRequest,
    ExpectedAnswerResponse, RAGEvaluationRequest, RAGEvaluationResult,
    ChunkInfo
)
from .utils import async_request
from .event_collector import log_rag_event
from level_core.evaluators.rag_evaluator import RAGEvaluator
from .prompts import build_expected_answer_messages, build_fallback_expected_messages
from .scraper import scrape_page
from .chat_client import post_chat

class RAGSimulator:
    
    def __init__(self, evaluation_service, generation_service, endpoint_base: str, chat_path: str, headers: Dict[str, str]):
        """
        Initialize RAG simulator.

        Args:
            evaluation_service: Service for evaluation operations
            generation_service: Service for expected answer generation
            endpoint_base: Chatbot base URL (e.g., http://localhost:8000)
            chat_path: Chat path (e.g., /chat)
            headers: HTTP headers for API calls
        """
        self.evaluation_service = evaluation_service
        self.generation_service = generation_service
        self.endpoint_base = endpoint_base.rstrip("/")
        self.chat_path = chat_path if chat_path.startswith("/") else f"/{chat_path}"
        self.headers = headers
        self.rag_evaluator = RAGEvaluator(
            generation_service=self.generation_service,
            evaluation_service=self.evaluation_service,
        )
        self.sessions = {}

    async def initialize_rag_and_scrape(self, request: RAGInitRequest) -> RAGInitResponse:
        """
        Step 1: Initialize RAG system and scrape page in one call.
        
        Args:
            request: RAG initialization request with page URL
            
        Returns:
            RAGInitResponse with initialization status and chunks
        """
        session_id = uuid4()
        session_id_str = str(session_id)
        log_rag_event("INFO", f"Starting RAG initialization and scraping for: {request.page_url}")
        
        endpoint_base = (request.chatbot_base_url or self.endpoint_base).rstrip("/")
        chat_path = (request.chatbot_chat_path if getattr(request, "chatbot_chat_path", None) else self.chat_path)
        chat_path = chat_path if chat_path.startswith("/") else f"/{chat_path}"

        init_payload = {"page_url": request.page_url}
        init_headers = {**self.headers, "x-model-id": request.model_id}
        
        init_response = await async_request(
            url=f"{endpoint_base}/init",
            headers=init_headers,
            payload=init_payload
        )
        
        if not init_response or init_response.status_code != 200:
            raise Exception(f"RAG initialization failed: {init_response.status_code if init_response else 'No response'}")
        
        scraped_chunks = await scrape_page(request.page_url, request.chunk_size)
        
        self.sessions[session_id_str] = {
            "page_url": request.page_url,
            "chunks": scraped_chunks,
            "chunk_size": request.chunk_size,
            "model_id": request.model_id,
            "endpoint_base": endpoint_base,
            "chat_path": chat_path,
            "created_at": datetime.now().isoformat()
        }
        
        log_rag_event("INFO", f"RAG initialized and scraped. Session: {session_id_str}")
        
        return RAGInitResponse(
            session_id=session_id,
            page_url=request.page_url,
            initialization_status="initialized",
            total_chunks=len(scraped_chunks),
            chunks=scraped_chunks,
            chunk_size=request.chunk_size
        )
    
    def _get_rag_evaluator(self, expected_model: Optional[str]) -> RAGEvaluator:
        if expected_model:
            return RAGEvaluator(
                generation_service=self.generation_service,
                evaluation_service=self.evaluation_service,
                expected_model=expected_model,
            )
        return self.rag_evaluator

    async def _retry_fallback_expected_answer(self, selected_chunks: List[str], prompt: str, expected_model: Optional[str]) -> str:
        alt_messages = build_fallback_expected_messages(selected_chunks, prompt)
        evaluator = self._get_rag_evaluator(expected_model)
        return await evaluator.generate_expected_answer(alt_messages)

    async def generate_expected_answer(self, request: ChunkSelectionRequest) -> ExpectedAnswerResponse:
        session_id = str(request.session_id)
        if session_id not in self.sessions:
            raise Exception(f"Session {session_id} not found. Available sessions: {list(self.sessions.keys())}")
        
        session_data = self.sessions[session_id]
        chunks = session_data["chunks"]
        
        log_rag_event("INFO", f"Generating expected answer for session: {session_id}")
        
        selected_chunks = [chunks[i].content for i in request.manual_order if i < len(chunks)]

        expected_model = getattr(request, "expected_model", None)

        try:
            previews = [textwrap.shorten(c, width=180, placeholder="...") for c in selected_chunks]
            log_rag_event("INFO", f"Selected chunk previews: {previews}")
        except Exception:
            pass

        messages = build_expected_answer_messages(selected_chunks, request.prompt)
        evaluator = self._get_rag_evaluator(expected_model)
        expected_answer = await evaluator.generate_expected_answer(messages)

        if expected_answer.strip() == "Not found in the provided context." and selected_chunks:
            log_rag_event("INFO", "Fallback triggered; retrying expected answer with summarization prompt")
            expected_answer = await self._retry_fallback_expected_answer(selected_chunks, request.prompt, expected_model)
        
        self.sessions[session_id]["expected_answer"] = expected_answer
        self.sessions[session_id]["selected_chunks"] = selected_chunks
        self.sessions[session_id]["prompt"] = request.prompt
        
        log_rag_event("INFO", "Expected answer generated successfully")
        
        return ExpectedAnswerResponse(
            session_id=request.session_id,
            prompt=request.prompt,
            generated_answer=expected_answer,
            selected_chunks=selected_chunks
        )
    
    async def evaluate_rag_retrieval(self, request: RAGEvaluationRequest) -> RAGEvaluationResult:
        start_time = time.time()
        session_id = str(request.session_id)
        
        if session_id not in self.sessions:
            raise Exception(f"Session {session_id} not found")
        
        session_data = self.sessions[session_id]
        
        log_rag_event("INFO", f"Starting RAG evaluation for session: {session_id}")
        
        t0 = time.time()
        chatbot_answer = await self._query_chatbot(
            request.prompt,
            session_data["model_id"],
            session_data.get("endpoint_base", self.endpoint_base),
            session_data.get("chat_path", self.chat_path),
        )
        t1 = time.time()
        
        self.sessions[session_id]["chatbot_answer"] = chatbot_answer
        
        # Run metrics computation and LLM comparison in parallel for better performance
        metrics_task = self.rag_evaluator.compute_metrics(
            expected=request.expected_answer,
            actual=chatbot_answer
        )
        compare_task = self.rag_evaluator.compare_answers(
            prompt=request.prompt,
            expected=request.expected_answer,
            actual=chatbot_answer
        )
        
        metrics, llm_comparison = await asyncio.gather(metrics_task, compare_task)
        t2 = time.time()
        t3 = t2  # Both tasks completed at the same time
        
        execution_time = time.time() - start_time

        self._log_phase_durations(t0, t1, t2, t3, execution_time)
        
        result = RAGEvaluationResult(
            session_id=request.session_id,
            page_url=session_data["page_url"],
            prompt=request.prompt,
            expected_answer=request.expected_answer,
            chatbot_answer=chatbot_answer,
            metrics=metrics,
            llm_comparison=llm_comparison,
            execution_time=execution_time,
            created_at=datetime.now().isoformat()
        )
        
        log_rag_event("INFO", "RAG evaluation completed successfully")
        return result

    def _log_phase_durations(self, t0, t1, t2, t3, total):
        log_rag_event(
            "INFO",
            "RAG evaluation durations (s)",
            {
                "chatbot_call": round(t1 - t0, 3),
                "metrics_and_judge_parallel": round(t2 - t1, 3),
                "total": round(total, 3),
            },
        )

    def cleanup_session(self, session_id: UUID) -> bool:
        sid = str(session_id)
        if sid in self.sessions:
            try:
                del self.sessions[sid]
                return True
            except Exception:
                return False
        return False
    
    async def _query_chatbot(self, prompt: str, model_id: str, endpoint_base: str, chat_path: str) -> str:
        """
        Query the chatbot service with a prompt and return its response.

        Args:
            prompt: The input prompt to send to the chatbot.
            model_id: The model identifier to use in the request headers.
            endpoint_base: Base URL of the chatbot service.
            chat_path: Path for the chat endpoint.

        Returns:
            The chatbot's response as a string.
        """
        log_rag_event("INFO", f"Querying chatbot with prompt: {prompt[:50]}...")
        headers = {**self.headers, "x-model-id": model_id}
        answer = await post_chat(endpoint_base, chat_path, headers, prompt)
        log_rag_event("INFO", "Chatbot response received")
        return answer