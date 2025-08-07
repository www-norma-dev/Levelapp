import os
import sys
import logging
import asyncio
from typing import List, Optional

from dotenv import load_dotenv

from level_core.evaluators.litellm_evaluator import LiteLLMEvaluator
from level_core.evaluators.schemas_litellm import LiteLLMConfig

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test")

def detect_providers_from_env() -> List[str]:
    """
    Detect LLM providers by scanning env vars for *_API_KEY entries.
    """
    env_vars = os.environ
    providers = set()

    for key in env_vars:
        if key.endswith("_API_KEY"):
            provider = key[:-8].lower()  # remove _API_KEY suffix
            providers.add(provider)

    return providers

def get_provider_config(provider_name: str) -> LiteLLMConfig:
    # Normalize to lowercase for internal handling
    provider_name = provider_name.lower()
    env_vars = os.environ

    # Use uppercase to match environment variable naming convention
    model_key = f"{provider_name.upper()}_MODEL"
    api_key_key = f"{provider_name.upper()}_API_KEY"
    api_base_key = f"{provider_name.upper()}_API_BASE"

    config = LiteLLMConfig(
        provider=provider_name,
        model=env_vars.get(model_key, "gpt-4o-mini"),
        api_key=env_vars.get(api_key_key),
        api_base=env_vars.get(api_base_key),
        additional_config={

        # Load per-provider values if set, fallback to defaults
        "temperature": float(env_vars.get(f"{provider_name.upper()}_TEMPERATURE", 0.0)),
        "max_tokens": int(env_vars.get(f"{provider_name.upper()}_MAX_TOKENS", 150)),

        }
    )
    return config

