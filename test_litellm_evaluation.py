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

    return sorted(providers)

def get_provider_config(provider_name: str) -> LiteLLMConfig:
    provider_name = provider_name.lower()
    env_vars = os.environ

    model_key = f"{provider_name.upper()}_MODEL"
    api_key_key = f"{provider_name.upper()}_API_KEY"
    api_base_key = f"{provider_name.upper()}_API_BASE"

    config = LiteLLMConfig(
        provider=provider_name,
        model=env_vars.get(model_key, "gpt-4o-mini"),
        api_key=env_vars.get(api_key_key),
        api_base=env_vars.get(api_base_key),
        additional_config={
            "temperature": float(env_vars.get("TEMPERATURE", 0.0)),
            "max_tokens": int(env_vars.get("MAX_TOKENS", 150)),
        }
    )
    return config

async def main():
    logger.info("Script started")

    providers = detect_providers_from_env()
    logger.info(f"Detected providers: {providers}")

    # Default to openai if, else first found, else error
    default_provider = "openai" if "openai" in providers else (providers[0] if providers else None)
    if default_provider is None:
        logger.error("No providers detected in environment. Please set *_API_KEY.")
        return

    # Provider can be passed as first CLI argument, else use DEFAULT_PROVIDER env var or default
    cli_provider: Optional[str] = sys.argv[1].lower() if len(sys.argv) > 1 else None
    env_default_provider = os.getenv("DEFAULT_PROVIDER", default_provider).lower()
    chosen_provider = cli_provider or env_default_provider

    if chosen_provider not in providers:
        logger.warning(f"Chosen provider '{chosen_provider}' not found in env, using default '{default_provider}'")
        chosen_provider = default_provider

    config = get_provider_config(chosen_provider)
    logger.info(f"Using provider: {config.provider} (model: {config.model})")

    evaluator = LiteLLMEvaluator(config)

    prompt = "What is the capital of France?"
    expected = "Paris"

    result = await evaluator.evaluate(prompt=prompt, expected_response=expected)

    logger.info("Evaluation completed")
    print("Match Level:", result.match_level)
    print("Justification:", result.justification)
    if result.metadata:
        print("Metadata:", result.metadata)

if __name__ == "__main__":
    asyncio.run(main())
