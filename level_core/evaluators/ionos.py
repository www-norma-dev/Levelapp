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
    def build_prompt(self, generated_text: str, expected_text: str) -> str:
        """
        Construct an evaluation prompt based on expected and generated text.

        Returns:
            str: Instructional prompt for the LLM to return a structured JSON evaluation.
        """
        return f"""
        You are an expert text evaluator. Your task is to evaluate how well the agent's generated text matches the expected text using semantic similarity, factual accuracy, and completeness.

        Use this exact 6-point scale (0-5):

        5 - Perfect Match: Generated text is semantically identical to expected text. All key information, meaning, and intent are preserved with only trivial differences (punctuation, minor word order).

        4 - Excellent Match: Generated text captures all essential meaning and information with minor stylistic differences. No important details are missing or incorrect.

        3 - Good Match: Generated text covers the main points accurately but may have some minor omissions, slight inaccuracies, or different phrasing that doesn't change core meaning.

        2 - Moderate Match: Generated text captures the general idea but has noticeable differences, missing details, or minor factual errors that somewhat impact accuracy.

        1 - Poor Match: Generated text addresses the topic but has significant omissions, factual errors, or substantially different meaning from expected text.

        0 - No Match: Generated text is completely unrelated, factually incorrect, or fails to address the expected content meaningfully.

        Expected Output:
        \"\"\"
        {expected_text}
        \"\"\"

        Agent's Generated Output:
        \"\"\"
        {generated_text}
        \"\"\"

        Evaluation Instructions:
        - Focus on semantic meaning rather than exact word matching
        - Consider whether someone reading the generated text would get the same information as from the expected text
        - Penalize factual inaccuracies more heavily than stylistic differences
        - Be consistent in your scoring across similar cases

        Return your evaluation as a valid JSON object with exactly these keys:
        {{"match_level": <integer from 0 to 5>, "justification": "<brief explanation of score reasoning>"}}

        Output only the JSON object and nothing else.
        """

    async def call_llm(self, prompt: str) -> Union[Dict, str]:
        """
        Send the evaluation prompt to the IONOS API and return the parsed response.

        Args:
            prompt (str): The text prompt to evaluate.

        Returns:
            Union[Dict, str]: A dictionary representing the evaluation result,
                              or an error message if the request fails.
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