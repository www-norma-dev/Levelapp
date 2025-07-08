"""
'evaluators/service.py': EvaluationService handles evaluator selection and execution for different providers.
"""
from logging import Logger
from typing import Literal, Dict

from pydantic import ValidationError

from .base import BaseEvaluator
from .ionos import IonosEvaluator
from .openai import OpenAIEvaluator
from .schemas import EvaluationConfig, EvaluationResult


class EvaluationService:
    """Service layer to manage evaluator configurations and orchestrate evaluations."""
    def __init__(self, logger: Logger):
        """
        Args:
            logger (Logger): Logger instance used across evaluators.
        """
        self.logger = logger
        self.configs: Dict[str, EvaluationConfig] = {}

    def set_config(self, provider: Literal["ionos", "openai"], config: EvaluationConfig):
        """
        Register an evaluation configuration for a specific provider.

        Args:
            provider (Literal): The evaluation provider ("ionos" or "openai").
            config (EvaluationConfig): The config object for that provider.
        """
        self.configs[provider] = config

    def _select_evaluator(self, provider: Literal["ionos", "openai"]) -> BaseEvaluator:
        """
        Factory method to return the correct evaluator instance.

        Args:
            provider (Literal): The name of the LLM provider.

        Returns:
            BaseEvaluator: Instantiated evaluator object.

        Raises:
            KeyError: If the provider or config is not found.
            ValueError: If the config is invalid.
        """
        evaluator_map = {
            "ionos": IonosEvaluator,
            "openai": OpenAIEvaluator,
        }

        try:
            config = self.configs[provider]
            return evaluator_map[provider](config, self.logger)
        except KeyError:
            raise KeyError(f"Invalid provider: {provider}. Valid providers: {list(self.configs.keys())}")
        except ValidationError as e:
            raise ValueError(f"Invalid configuration: {e.errors()}")

    async def evaluate_response(
            self,
            provider: Literal["ionos", "openai"],
            output_text: str,
            reference_text: str
    ) -> EvaluationResult:
        """
        Perform evaluation using the configured provider.

        Args:
            provider (Literal): Evaluation provider to use.
            output_text (str): Generated output from the agent.
            reference_text (str): Expected output to compare against.

        Returns:
            EvaluationResult: The structured evaluation result.

        Raises:
            ValueError: If the provider has not been configured.
        """
        if provider not in self.configs:
            raise ValueError(f"[evaluate_response] No configuration set for provider: {provider}")

        evaluator = self._select_evaluator(provider=provider)
        return await evaluator.evaluate(generated_text=output_text, expected_text=reference_text)
