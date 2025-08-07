import os
import logging
import asyncio
from typing import Optional

import openai

from .schemas_litellm import LiteLLMConfig, EvaluationResult

logger = logging.getLogger("LiteLLMEvaluator")

class LiteLLMEvaluator:
    def __init__(self, config: LiteLLMConfig):
        self.config = config

        # Load API key, prefer config value, else fallback to env vars
        api_key = config.api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("No OpenAI API key found in config or environment.")

        openai.api_key = api_key
        if config.api_base:
            openai.api_base = config.api_base

        self.client = openai.OpenAI()

    async def evaluate(self, prompt: str, expected_response: str) -> EvaluationResult:
        eval_prompt = (
            f"Output: {prompt}\n"
            f"Expected: {expected_response}\n"
            f"Is the output correct? provide a short justification."
        )

        loop = asyncio.get_running_loop()

        def sync_call():
            return self.client.chat.completions.create(
                model=self.config.model,
                messages=[{"role": "user", "content": eval_prompt}],
                temperature=self.config.additional_config.get("temperature", 0.0),
                max_tokens=self.config.additional_config.get("max_tokens", 150),
            )

        try:
            response = await loop.run_in_executor(None, sync_call)
            generated_text = response.choices[0].message.content.strip()

            match_level = 1.0 if "yes" in generated_text.lower() else 0.0

            logger.info(f"Generated justification: {generated_text}")

            return EvaluationResult(
                match_level=match_level,
                justification=generated_text,
                metadata={"output": prompt, "expected": expected_response}
            )
        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            return EvaluationResult(
                match_level=0.0,
                justification=f"Evaluation failed: {e}",
                metadata={}
            )
