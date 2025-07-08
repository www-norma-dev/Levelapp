"""
'evaluators/ionos.py': IONOS-based LLM evaluator implementation.

This module defines a concrete implementation of the `BaseEvaluator` class
using IONOS-hosted language models for evaluating generated vs expected text.
"""

import uuid
import httpx

from typing import Union, Dict

from evaluators.base import BaseEvaluator


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

                ## Removed business-specific metadata keys and generalized the metadata section
                metadata = {
                    "input_tokens": response.json().get("metadata", {}).get("inputTokens"),
                    "output_tokens": response.json().get("metadata", {}).get("outputTokens"),
                }
                parsed_output["metadata"] = metadata

                return parsed_output or {"error": "Empty API response"}

        except httpx.RequestError as req_err:
            self.logger.error("IONOS API request failed: %s", str(req_err), exc_info=True)
            return {"error": "API request failed", "details": str(req_err)}
