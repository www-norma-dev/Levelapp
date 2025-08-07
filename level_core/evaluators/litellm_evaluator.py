import os
import logging
import asyncio
from typing import Optional

import litellm

from .schemas_litellm import LiteLLMConfig, EvaluationResult

logger = logging.getLogger("LiteLLMEvaluator")


class LiteLLMEvaluator:
    def __init__(self, config: LiteLLMConfig):
        self.config = config
        
        if not config.model:
            logger.warning("No API key found in config or environment.")

        # Logging for transparency
        logger.info(f"Using model: {self.config.model}")
        logger.info(f"Additional config: {self.config.additional_config}")

    async def evaluate(self, prompt: str, expected_response: str) -> EvaluationResult:
        eval_prompt = (
            f"Output: {prompt}\n"
            f"Expected: {expected_response}\n"
            f"Is the output correct? provide a short justification."
        )

        loop = asyncio.get_running_loop()

        def sync_call():
            return litellm.completion(
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
                metadata={"model": self.config.model,"output": prompt, "expected": expected_response}
            )
        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            return EvaluationResult(
                match_level=0.0,
                justification=f"Evaluation failed: {e}",
                metadata={}
            )
