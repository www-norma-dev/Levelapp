"""
'evaluators/service.py': EvaluationService handles evaluator selection and execution for different providers.
"""

from logging import Logger
from typing import Dict, Optional, Type

from pydantic import ValidationError

from .base import BaseEvaluator
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

        # New attribute to hold evaluator classes
        # This allows dynamic registration of evaluators by their provider name
        
        self.evaluator_classes: Dict[str, Type[BaseEvaluator]] = {}

    def register_evaluator(self, provider: str, evaluator_cls: Type[BaseEvaluator]):
        """
        Enregistre un évaluateur dynamique par son nom (provider).

        Args:
            provider (str): Nom de l'évaluateur.
            evaluator_cls (Type[BaseEvaluator]): Classe de l'évaluateur.
        """
        self.evaluator_classes[provider] = evaluator_cls
        if self.logger:
            self.logger.info(f"Evaluator '{provider}' registered.")

    def set_config(self, provider: str, config: EvaluationConfig):
        """
        Register an evaluation configuration for a specific provider.

        Args:
            provider (str): The evaluation provider identifier.
            config (EvaluationConfig): The config object for that provider.
        """
        self.configs[provider] = config

    def _select_evaluator(self, provider: str) -> BaseEvaluator:
        """
        Factory method to return the correct evaluator instance.

        Args:
            provider (str): The name of the evaluator provider.

        Returns:
            BaseEvaluator: Instantiated evaluator object.

        Raises:
            KeyError: If the provider or config is not found.
            ValueError: If the config is invalid.
        """
        if provider not in self.evaluator_classes:
            raise KeyError(f"Evaluator '{provider}' is not registered.")

        if provider not in self.configs:
            raise KeyError(f"No configuration found for evaluator '{provider}'.")

        evaluator_cls = self.evaluator_classes[provider]
        config = self.configs[provider]

        try:
            return evaluator_cls(config, self.logger)
        except ValidationError as e:
            raise ValueError(f"Invalid configuration: {e.errors()}")

    async def evaluate_response(
        self,
        provider: str,  #  accept generic str
        output_text: str,
        reference_text: str
    ) -> EvaluationResult:
        """
        Perform evaluation using the configured provider.

        Args:
            provider (str): Evaluation provider to use.
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
