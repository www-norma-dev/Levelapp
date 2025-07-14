"""
'evaluators/base.py': Base class for all LLM-based evaluators.

This module defines an abstract interface and common logic for evaluating
generated text against expected outcomes using LLMs. Specific implementations
(e.g., OpenAI, IONOS, Claude, Mistral) should subclass `BaseEvaluator`.
"""

import re
import json
import uuid
import logging
from abc import ABC, abstractmethod
from typing import Union, Dict

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from pydantic import ValidationError

from evaluators.schemas import EvaluationConfig, EvaluationResult

logger = logging.getLogger(__name__)


class BaseEvaluator(ABC):
    """Abstract base class for implementing text evaluation via LLMs."""

    def __init__(self, config: EvaluationConfig):
        """
        Initialize the evaluator with configuration.

        Args:
            config (EvaluationConfig): Configuration for evaluation behavior.

        """
        self.config = config

    @abstractmethod
    def build_prompt(self, generated_text: str, expected_text: str) -> str:
        """
        Construct a prompt to send to the LLM for evaluation.

        Args:
            generated_text (str): Text produced by the model under test.
            expected_text (str): Reference or ground-truth text.

        Returns:
            str: The formatted prompt to pass to the LLM.
        """
        pass

    @abstractmethod
    async def call_llm(self, prompt: str) -> Union[Dict, str]:
        """
        Make a call to the LLM with a given prompt.

        Args:
            prompt (str): The prompt string to evaluate.

        Returns:
            Union[Dict, str]: Either a parsed dict or a raw string response.
        """
        pass

    @staticmethod
    def _parse_json_output(output: str) -> Dict:
        """
        Safely parse JSON string output from LLM.

        Uses regex as a fallback to extract JSON-like structure if direct parsing fails.

        Args:
            output (str): Raw output string from the LLM.

        Returns:
            Dict: Parsed output dictionary or an error message.
        """
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            match = re.search(r"(\{.*\})", output, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    pass
            return {"error": "Invalid JSON output"}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def evaluate(self, generated_text: str, expected_text: str) -> EvaluationResult:
        """
        Evaluate generated text against expected text using an LLM.

        Handles retry logic and fallback parsing for robustness.

        Args:
            generated_text (str): The model-generated response.
            expected_text (str): The expected or reference response.

        Returns:
            EvaluationResult: Structured result of the evaluation.
        """
        logger.debug("Building prompt for evaluation")
        prompt = self.build_prompt(generated_text, expected_text)

        response = await self.call_llm(prompt)

        if isinstance(response, dict):
            try:
                return EvaluationResult.model_validate(response)
            except ValidationError as e:
                logger.error(f"Pydantic validation failed: {e}")
                return None

        logger.warning("LLM returned unexpected response format")
        return EvaluationResult(
            match_level=0,
            justification=f"Evaluation failed: {response}"
        )


class ClaudeEvaluator(BaseEvaluator):
    """Evaluator that uses the Claude API to score model responses."""

    def build_prompt(self, generated_text: str, expected_text: str) -> str:
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
    "match_level": <an integer between 0 and 3>,
    "justification": <a brief explanation>
}}

Output only the JSON object and nothing else.
"""

    def _prepare_claude_request(self, prompt: str) -> Dict:
        url = f"{self.config.api_url}/v1/complete"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "prompt": prompt,
            "model": self.config.model_id or "claude-v1",
            "max_tokens_to_sample": 1000,
            "temperature": 0,
            "stop_sequences": ["\n\n"],
            "user": str(uuid.uuid4()),
            **(self.config.llm_config or {}),
        }
        return {"url": url, "headers": headers, "json": payload}

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type(httpx.RequestError),
    )
    async def call_llm(self, prompt: str) -> Union[Dict, str]:
        req = self._prepare_claude_request(prompt)

        async with httpx.AsyncClient(timeout=300) as client:
            response = await client.post(
                url=req["url"],
                headers=req["headers"],
                json=req["json"],
            )
            response.raise_for_status()
            response_json = response.json()
            output = response_json.get("completion", "").strip()
            parsed_output = self._parse_json_output(output)

            metadata = response_json.get("metadata", {})
            if metadata:
                parsed_output["metadata"] = metadata

            return parsed_output or {"error": "Empty API response"}

    async def safe_call_llm(self, prompt: str) -> Union[Dict, str]:
        try:
            return await self.call_llm(prompt)
        except Exception as exc:
            logger.error("Claude evaluation failed: %s", exc, exc_info=True)
            return {"error": "API request failed", "details": str(exc)}


class MistralEvaluator(BaseEvaluator):
    """Evaluator that uses the Mistral API to score model responses."""

    def build_prompt(self, generated_text: str, expected_text: str) -> str:
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
        url = self.config.api_url or "https://api.mistral.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.config.model_id or "mistral-medium",
            "messages": [{"role": "user", "content": prompt}],
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
        req = self._prepare_mistral_request(prompt)

        async with httpx.AsyncClient(timeout=300) as client:
            response = await client.post(
                url=req["url"],
                headers=req["headers"],
                json=req["json"],
            )
            response.raise_for_status()
            response_json = response.json()
            content = response_json.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            parsed_output = self._parse_json_output(content)

            metadata = response_json.get("usage", {})
            if metadata:
                parsed_output["metadata"] = metadata

            return parsed_output or {"error": "Empty API response"}

    async def safe_call_llm(self, prompt: str) -> Union[Dict, str]:
        try:
            return await self.call_llm(prompt)
        except Exception as exc:
            logger.error("Mistral evaluation failed: %s", exc, exc_info=True)
            return {"error": "API request failed", "details": str(exc)}
