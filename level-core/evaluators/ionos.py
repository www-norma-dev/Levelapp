"""
'evaluators/ionos.py': IONOS-based LLM evaluator implementation.

This module defines a concrete implementation of the `BaseEvaluator` class
using IONOS-hosted language models for evaluating generated vs expected text.
"""

import uuid
import httpx
import logging                         # for optional module-level logging
from typing import Union, Dict

# NEW: Tenacity imports for retry logic
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from evaluators.base import BaseEvaluator

logger = logging.getLogger(__name__)   # fallback logger 


class IonosEvaluator(BaseEvaluator):
    """Evaluator that uses the IONOS inference API to score model responses."""

    def build_prompt(self, generated_text: str, expected_text: str) -> str:
        """
        Construct an evaluation prompt based on expected and generated text.

        Returns:
            str: Instructional prompt for the LLM to return a structured JSON evaluation.
        """
        return f"""
        Your task is to evaluate how well the model's generated text matches the expected reference.

        Use the following classification criteria:
        3 - Excellent Match: The generated text is virtually identical to the expected text with no meaningful differences.
        2 - Good Match: The generated text closely matches the expected text with only minor wording differences.
        1 - Moderate Match: The generated text captures the main ideas but has noticeable differences or omissions.
        0 - Poor Match: The generated text has significant differences and misses several key points.

        Expected Output:
        \"\"\" 
        {expected_text}
        \"\"\"

        Generated Text:
        \"\"\" 
        {generated_text}
        \"\"\"

        Return your evaluation as a valid JSON object with exactly these keys:
        {{
            "match_level": <an integer between 0 and 3>,  ## generalized scale (can be extended in future)
            "justification": <a brief explanation>
        }}

        Output only the JSON object and nothing else.
        """
#        NEW METHOD: Extracted from `call_llm` to isolate endpoint configuration logic.
#        This prepares the URL, headers, and payload for the IONOS API request.

    def _prepare_ionos_request(self, prompt: str) -> Dict:
        """

        Args:
            prompt (str): The evaluation prompt.

        Returns:
            Dict: A dictionary with `url`, `headers`, and `payload` keys.
        """
        url = f"{self.config.api_url}/{self.config.model_id}/predictions"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "properties": {"input": prompt},
            "option": {
                **self.config.llm_config,
                "seed": uuid.uuid4().int & ((1 << 16) - 1),
            }
        }
        return {"url": url, "headers": headers, "payload": payload}

    @retry(                 # Changes here: using Tenacity for retry logic
        stop=stop_after_attempt(3),                      # retry up to 3 times
        wait=wait_exponential(multiplier=1, min=1, max=8),  # exponential backoff (1s, 2s, 4s)
        retry=retry_if_exception_type(httpx.RequestError)  # only retry on network-level failures
    )
    async def call_llm(self, prompt: str) -> Union[Dict, str]:
        """
        Send the evaluation prompt to the IONOS API and return the parsed response.
        Automatically retries up to 3 times on network errors.

        Args:
            prompt (str): The text prompt to evaluate.

        Returns:
            Union[Dict, str]: A dictionary representing the evaluation result,
                              or an error message if the request fails.
        """
        req = self._prepare_ionos_request(prompt)  # CHANGED: Using now the new helper method for setup

        async with httpx.AsyncClient(timeout=300) as client:
            response = await client.post(
                url=req["url"],
                headers=req["headers"],
                json=req["payload"]
            )
            response.raise_for_status()                  # raises for 4xx/5xx → caught by Tenacity

            output = response.json().get("properties", {}).get("output", "").strip()
            parsed_output = self._parse_json_output(output)

            metadata = {
                "input_tokens": response.json().get("metadata", {}).get("inputTokens"),
                "output_tokens": response.json().get("metadata", {}).get("outputTokens"),
            }
            parsed_output["metadata"] = metadata

            return parsed_output or {"error": "Empty API response"}

    async def safe_call_llm(self, prompt: str) -> Union[Dict, str]:
        """
        Wrapper that calls `call_llm` with retry and catches any remaining errors.
        Use this method from outside instead of `call_llm` directly.

        Args:
            prompt (str): The text prompt to evaluate.

        Returns:
            Union[Dict, str]: The evaluation result or an error message.
        """
        try:
            return await self.call_llm(prompt)
        except Exception as exc:                          # anything Tenacity didn't handle will be caught here
            logger.error("IONOS evaluation failed: %s", exc, exc_info=True)
            return {"error": "API request failed", "details": str(exc)}
