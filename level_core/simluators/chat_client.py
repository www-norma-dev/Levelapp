"""
Async chat client helper with fallback behavior.
"""
from typing import Dict

from .utils import async_request
from .event_collector import log_rag_event


async def post_chat(endpoint_base: str, chat_path: str, headers: Dict[str, str], prompt: str) -> str:
    payload = {"prompt": prompt}
    eb = endpoint_base.rstrip("/")
    cp = chat_path if chat_path.startswith("/") else f"/{chat_path}"
    primary_url = f"{eb}{cp}"
    log_rag_event("INFO", f"Chatbot POST URL: {primary_url}")

    response = await async_request(
        url=primary_url,
        headers=headers,
        payload=payload,
    )

    if (not response or response.status_code != 200) and cp != "/":
        fallback_url = f"{eb}/"
        log_rag_event("WARN", f"Primary chat URL failed; retrying at {fallback_url}")
        response = await async_request(
            url=fallback_url,
            headers=headers,
            payload=payload,
        )

    if not response or response.status_code != 200:
        raise Exception(f"Chatbot query failed: {response.status_code if response else 'No response'}")

    data = response.json()
    if isinstance(data, dict) and "response" in data:
        return str(data["response"])
    return str(data)
