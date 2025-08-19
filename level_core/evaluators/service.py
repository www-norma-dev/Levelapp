"""
'evaluators/service.py': EvaluationService handles evaluator selection and execution for different providers.
"""

import os
from logging import Logger
from typing import Dict, Literal

from pydantic import ValidationError

from .base import BaseEvaluator
from .schemas import EvaluationConfig, EvaluationResult
from .openai import OpenAIEvaluator
from .ionos import IonosEvaluator
from .utils import extract_key_point
from config.loader import load_config


class EvaluationService:
    """Service layer to manage evaluator configurations and orchestrate evaluations."""
    def __init__(self, logger: Logger):
        """
        Args:
            logger (Logger): Logger instance used across evaluators.
        """
        self.logger = logger

        # Load provider configs directly from YAML at root folder
        # IMPORTANT: expand ${ENV_VAR} from .env / environment
        full_config = load_config("config.yaml")
        self.configs: Dict[str, EvaluationConfig] = {}

        providers = full_config.get("providers", {}) or {}
        for provider_name, raw_cfg in providers.items():
            try:
                cfg = {
                    "api_key": os.path.expandvars(raw_cfg.get("api_key", "")),
                    "api_url": os.path.expandvars(raw_cfg.get("api_url", "")),
                    "model_id": os.path.expandvars(raw_cfg.get("model_id", "")),
                }

                # Skip providers without an API key
                if not cfg["api_key"]:
                    self.logger.warning(
                        f"[EvaluationService] Skipping provider '{provider_name}' (missing API key)."
                    )
                    continue

                self.configs[provider_name] = EvaluationConfig(**cfg)

            except ValidationError as e:
                self.logger.error(
                    f"[EvaluationService] Invalid config for provider '{provider_name}': {e.errors()}"
                )
            except Exception as e:
                self.logger.error(
                    f"[EvaluationService] Failed to load provider '{provider_name}': {e}"
                )

        self.logger.info(f"[EvaluationService] Loaded providers: {list(self.configs.keys())}")

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

        if provider not in self.configs:
            raise KeyError(
                f"Invalid or unconfigured provider: {provider}. "
                f"Available: {list(self.configs.keys())}"
            )

        try:
            config = self.configs[provider]
            return evaluator_map[provider](config, self.logger)
        except KeyError:
            raise KeyError(
                f"No evaluator defined for provider '{provider}'. "
                f"Supported: {list(evaluator_map.keys())}"
            )
        except ValidationError as e:
            raise ValueError(f"Invalid configuration for '{provider}': {e.errors()}")

    async def evaluate_response(self,provider: Literal["ionos", "openai"],
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

        try:
            result = await evaluator.evaluate(
                generated_text=output_text,
                expected_text=reference_text,
                user_message=user_message
            )
        except Exception as e:
            # Do NOT crash the whole request; return a structured failure for this provider
            self.logger.error(f"[evaluate_response] {provider} evaluation failed: {e}")
            # Create a minimal failed result object compatible with your schema
            result = EvaluationResult(
                match_level=0,
                justification="",
                metadata={"error": str(e)}
            )

        # Post-process: deterministic key point extraction
        kp_user = extract_key_point(user_message or "") if user_message else ""
        kp_expected = extract_key_point(reference_text)
        kp_generated = extract_key_point(output_text)
        result.metadata = result.metadata or {}
        result.metadata.update({
            "user_key_point": kp_user,
            "expected_key_point": kp_expected,
            "generated_key_point": kp_generated,
            "key_point_method": "heuristic_v1"
        })
        return result
