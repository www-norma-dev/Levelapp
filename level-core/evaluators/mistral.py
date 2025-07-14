"""
'evaluators/mistral.py': Mistral-based LLM evaluator implementation.

This module defines a concrete implementation of the `BaseEvaluator` class
using Mistral language models for evaluating generated vs expected text.
"""

import uuid
import httpx
import logging
from typing import Union, Dict

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from evaluators.base import BaseEvaluator

logger = logging.getLogger(__name__)


class MistralEvaluator(BaseEvaluator):
    """Evaluator that uses the Mistral API to score model responses."""

    def build_prompt(self, generated_text: str, expected_text: str) -> str:
        """
        Construct an evaluation prompt based on expected and generated text.

        Returns:
            str: Instructional prompt for the LLM to return a structured JSON evaluation.
        """
        return f"""
You are to score the generated text against the expected text.

Generated Text:
\"\"\"
{generated_text}
\"\"\"

Expected Text:
\"\"\"
{expected_text}
\"\"\"

Respond with a JSON object containing:
{{
  "match_level": <integer between 0 and 3>,
  "justification": "<brief explanation>"
}}

Output only the JSON object and nothing else.
"""

    def _prepare_mistral_request(self, prompt: str) -> Dict:
        """
        Prepare the Mistral API request details.

        Args:
            prompt (str): The evaluation prompt.

        Returns:
            Dict: A dictionary with url, headers, and json payload.
        """
        url = self.config.api_url or "https://api.mistral.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.config.model_id or "mistral-medium",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.0,
            **(self.config.llm_config or {}),
        }
        return {"url": url, "headers": headers, "json": payload}

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type(httpx.RequestError),
    )
    async def call_llm(self, prompt: str) -> Union[Dict, str]:
        """
        Send the evaluation prompt to the Mistral API and return the parsed response.
        Retries network errors automatically.

        Args:
            prompt (str): The text prompt to evaluate.

        Returns:
            Union[Dict, str]: Parsed evaluation result or error message.
        """
        req = self._prepare_mistral_request(prompt)

        async with httpx.AsyncClient(timeout=300) as client:
            response = await client.post(
                url=req["url"],
                headers=req["headers"],
                json=req["json"]
            )
            response.raise_for_status()

            response_json = response.json()
            content = (
                response_json.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
                .strip()
            )
            parsed_output = self._parse_json_output(content)

            metadata = response_json.get("usage", {})
            if metadata:
                parsed_output["metadata"] = metadata

            return parsed_output or {"error": "Empty API response"}

    async def safe_call_llm(self, prompt: str) -> Union[Dict, str]:
        """
        Wrapper to safely call `call_llm` with exception handling.

        Args:
            prompt (str): The text prompt to evaluate.

        Returns:
            Union[Dict, str]: The evaluation result or an error message.
        """
        try:
            return await self.call_llm(prompt)
        except Exception as exc:
            logger.error("Mistral evaluation failed: %s", exc, exc_info=True)
            return {"error": "API request failed", "details": str(exc)}
