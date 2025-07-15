from evaluators.generic_api import GenericAPIEvaluator
from evaluators.openai import OpenAIEvaluator
from evaluators.ionos import IonosEvaluator
from evaluators.schemas import EvaluationConfig

from logging import getLogger

def get_evaluator(config: EvaluationConfig):
    provider = config.provider.lower()
    logger = getLogger(f"{provider}-evaluator")

    if provider == "openai":
        return OpenAIEvaluator(config, logger)
    elif provider == "ionos":
        return IonosEvaluator(config, logger)
    else:
        return GenericAPIEvaluator(config, logger)
