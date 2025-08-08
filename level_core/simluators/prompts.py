"""
Prompt builders for RAG workflows.
"""
from typing import List, Dict

from .event_collector import log_rag_event
from .constants import MAX_CONTEXT_CHARS, CONTEXT_JOIN_SEPARATOR


def build_expected_answer_messages(selected_chunks: List[str], question: str, max_context_chars: int = MAX_CONTEXT_CHARS) -> List[Dict[str, str]]:
    """Build a single, well-structured prompt to force grounding in selected chunks."""
    context = CONTEXT_JOIN_SEPARATOR.join(selected_chunks)
    if len(context) > max_context_chars:
        context = context[:max_context_chars]

    system_msg = {
        "role": "system",
        "content": (
            "You are a precise answer extractor. Answer the QUESTION strictly based on the provided CONTEXT. "
            "Synthesize across multiple parts of the CONTEXT when needed. Be concise and factual. "
            "If the answer truly isn't supported by the CONTEXT, reply exactly: 'Not found in the provided context.'"
        ),
    }
    user_msg = {
        "role": "user",
        "content": (
            f"CONTEXT:\n{context}\n\n"
            f"QUESTION:\n{question}\n\n"
            f"Answer using only the CONTEXT. If the question asks for features/services/details, summarize precisely."
        ),
    }

    try:
        preview = (user_msg["content"][:400] + "...") if len(user_msg["content"]) > 400 else user_msg["content"]
        log_rag_event("INFO", f"EXPECTED_ANSWER_PROMPT_PREVIEW: {preview}")
    except Exception:
        pass

    return [system_msg, user_msg]


def build_fallback_expected_messages(selected_chunks: List[str], question: str, max_context_chars: int = MAX_CONTEXT_CHARS) -> List[Dict[str, str]]:
    """Build a gentler summarization prompt for fallback generation."""
    context = CONTEXT_JOIN_SEPARATOR.join(selected_chunks)
    if len(context) > max_context_chars:
        context = context[:max_context_chars]

    system_msg = {
        "role": "system",
        "content": (
            "Summarize the key facts from the CONTEXT that answer the QUESTION. "
            "Only use information present in CONTEXT. If nothing relevant exists, reply exactly: 'Not found in the provided context.'"
        ),
    }
    user_msg = {
        "role": "user",
        "content": (
            f"CONTEXT:\n{context}\n\n"
            f"QUESTION:\n{question}\n\n"
            f"Answer concisely using only the CONTEXT."
        ),
    }
    return [system_msg, user_msg]
