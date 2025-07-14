"""evaluators/claude.py: Claude evaluator module"""
from typing import Dict, Any
import httpx
import logging

logger = logging.getLogger("claude-evaluator")

API_URL = "https://api.anthropic.com/v1/messages"
API_KEY = "claude_api_key"

HEADERS = {
    "x-api-key": API_KEY,
    "anthropic-version": "2023-06-01",
    "Content-Type": "application/json"
}


def call_claude(prompt: str, model: str = "claude-3-opus-20240229") -> str:
    try:
        response = httpx.post(
            url=API_URL,
            headers=HEADERS,
            json={
                "model": model,
                "max_tokens": 1024,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            },
            timeout=60
        )
        response.raise_for_status()
        data = response.json()
        return data["content"][0]["text"]
    except Exception as e:
        logger.error(f"Claude API error: {str(e)}", exc_info=True)
        return "Claude API call failed."
