"""
'evaluators/base.py': Base class for all LLM-based evaluators.

This module defines an abstract interface and common logic for evaluating
generated text against expected outcomes using LLMs. Specific implementations
(e.g., OpenAI, IONOS) should subclass `BaseEvaluator`.
"""
import re
import json

from abc import ABC, abstractmethod
from logging import Logger
from typing import Union, Dict

from tenacity import stop_after_attempt, wait_exponential, retry

from evaluators.schemas import EvaluationConfig, EvaluationResult


class BaseEvaluator(ABC):
    """Abstract base class for implementing text evaluation via LLMs."""
    def __init__(self, config: EvaluationConfig, logger: Logger):
        """
        Initialize the evaluator with configuration and logger.

        Args:
            config (EvaluationConfig): Configuration for evaluation behavior.
            logger (Logger): Logger instance for structured logging.
        """
        self.config = config
        self.logger = logger

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
        prompt = self.build_prompt(generated_text, expected_text)
        response = await self.call_llm(prompt)

        if isinstance(response, dict):
            return EvaluationResult.model_validate(response)
        return EvaluationResult(
            match_level=0,
            justification=f"Evaluation failed: {response}"
        )
