import os
import logging
import asyncio
from typing import Optional

import litellm
from litellm.exceptions import AuthenticationError
from .schemas import EvaluationConfig, EvaluationResult


logger = logging.getLogger("LiteLLMEvaluator")


class LiteLLMEvaluator:
    """
    Evaluates LLM outputs against expected responses using LiteLLM.
    Falls back to IONOS if no model_id is provided.
    """

    def __init__(self, config: EvaluationConfig):
        self.config = config
        
        if not config.model_id:
            logger.warning("No model_id provided. Switching to OpenAI default.")
            self.config.model_id = "gpt-4o-mini"  # default OpenAI model
            self.config.api_key = os.getenv("OPENAI_API_KEY")
            self.config.api_url = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
            if not self.config.api_key:
                logger.error("OpenAI API key is missing. Please set OPENAI_API_KEY.")
                raise ValueError("Missing OpenAI API key.")

        # Logging for transparency
        logger.info(f"Using model: {self.config.model_id} | Additional config: {self.config.llm_config}")



    async def evaluate(self, prompt: str, expected_response: str, attempted_fallback=False) -> EvaluationResult:
        eval_prompt = f"""Output: {prompt}
                        Expected: {expected_response}
                        Is the output correct? Provide a short justification."""




        loop = asyncio.get_running_loop()

        def sync_call():
            return litellm.completion(
                model=self.config.model_id,
                messages=[{"role": "user", "content": eval_prompt}],
                temperature=self.config.llm_config.get("temperature", 0.0),
                max_tokens=self.config.llm_config.get("max_tokens", 150),
                api_base=self.config.api_url,
                api_key=self.config.api_key,
            )

        try:
            response = await loop.run_in_executor(None, sync_call)
            generated_text = response.choices[0].message.content.strip()

            match_level = 1.0 if "yes" in generated_text.lower() else 0.0

            logger.info(f"Generated justification: {generated_text}")

            return EvaluationResult(
                match_level=match_level,
                justification=generated_text,
                metadata={"model": self.config.model_id,"output": prompt, "expected": expected_response}
            )
        except AuthenticationError as e:
            if attempted_fallback:
                logger.error("Fallback to OpenAI also failed.")
                return EvaluationResult(
                    match_level=0.0,
                    justification="Authentication failed with OpenAI as well. "
                                "Please verify your API key at https://platform.openai.com/account/api-keys "
                                "and set it as the OPENAI_API_KEY environment variable.",
                    metadata={"error": str(e)}
                )

            logger.warning(f"Auth failed for {self.config.model_id}, retrying with OpenAI fallback...")
            self.config.model_id = os.getenv("OPENAI_MODEL_ID", "gpt-4o-mini")
            self.config.api_key = os.getenv("OPENAI_API_KEY")
            self.config.api_url = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")

            if not self.config.api_key:
                logger.error("OpenAI API key missing. Cannot continue.")
                return EvaluationResult(
                    match_level=0.0,
                    justification="OpenAI API key is missing. Please set OPENAI_API_KEY environment variable.",
                    metadata={}
                )

            return await self.evaluate(prompt, expected_response, attempted_fallback=True)


        except Exception as e:
            logger.exception(f"Evaluation failed.")
            return EvaluationResult(
                match_level=0.0,
                justification=f"Evaluation failed: {e}",
                metadata={}
            )