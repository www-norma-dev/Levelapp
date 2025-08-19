"""
'evaluators/ionos.py': IONOS-based LLM evaluator implementation.

This module defines a concrete implementation of the `BaseEvaluator` class
using IONOS-hosted language models for evaluating generated vs expected text.
"""
import uuid
import httpx
from logging import Logger
from typing import Union, Dict

from .base import BaseEvaluator


class IonosEvaluator(BaseEvaluator):
    """Evaluator that uses the IONOS inference API to score agent responses."""

    def build_prompt(self, user_message: str | None, generated_text: str, expected_text: str) -> str:
        """Construct evaluation prompt (score + justification only)."""
        user_msg = user_message or "(no user message provided)"
        return "\n".join([
            "You are an expert text evaluator. Compare generated text to expected text for semantic similarity, factual accuracy, completeness.",
            "Provide a score 0-5 and a concise justification (<=35 words).",
            "Scoring: 5 perfect; 4 excellent minor style diffs; 3 good minor omissions; 2 moderate noticeable gaps; 1 poor major issues; 0 no match.",
            "User Message:", '"""', user_msg, '"""',
            "Expected:", '"""', expected_text, '"""',
            "Generated:", '"""', generated_text, '"""',
            "Return ONLY JSON: {\"match_level\": <0-5>, \"justification\": \"<reason>\", \"metadata\": {}}",
        ])

    async def call_llm(self, prompt: str) -> Union[Dict, str]:
        """Send the evaluation prompt to the IONOS API and return parsed response."""
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

        try:
            async with httpx.AsyncClient(timeout=300) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()

                output = response.json().get("properties", {}).get("output", "").strip()
                parsed_output = self._parse_json_output(output)

                metadata = {
                    "inputTokens": response.json().get("metadata", {}).get("inputTokens"),
                    "outputTokens": response.json().get("metadata", {}).get("outputTokens"),
                }
                parsed_output["metadata"] = metadata

                return parsed_output or {"error": "Empty API response"}

        except httpx.RequestError as req_err:
            self.logger.error("IONOS API request failed: %s", str(req_err), exc_info=True)
            return {"error": "API request failed", "details": str(req_err)}