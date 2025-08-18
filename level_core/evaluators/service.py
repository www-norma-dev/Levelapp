"""
'evaluators/service.py': EvaluationService handles evaluator selection and execution for different providers.
"""

from logging import Logger
from typing import Dict, Optional, Type, Literal

from pydantic import ValidationError

from .base import BaseEvaluator
from .schemas import EvaluationConfig, EvaluationResult
from .openai import OpenAIEvaluator
from .ionos import IonosEvaluator
from .utils import extract_key_point

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
            reference_text: str,
            user_message: str | None = None
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
        result = await evaluator.evaluate(generated_text=output_text, expected_text=reference_text, user_message=user_message)
        # Post-process: deterministic key point extraction (overrides any LLM hallucinated ones)
        kp_user = extract_key_point(user_message or "") if user_message else ""
        kp_expected = extract_key_point(reference_text)
        kp_generated = extract_key_point(output_text)
        result.metadata = result.metadata or {}
        # Only set if missing to allow future override preference; but user wants reliable => overwrite
        result.metadata.update({
            "user_key_point": kp_user,
            "expected_key_point": kp_expected,
            "generated_key_point": kp_generated,
            "key_point_method": "heuristic_v1"
        })
        return result
