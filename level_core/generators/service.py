"""
'generators/service.py': GenerationService handles text generation across providers.
Mirrors EvaluationService (provider + messages -> text output).
"""
from typing import Dict, Literal, List, Optional
from logging import Logger

from pydantic import BaseModel


class GenerationConfig(BaseModel):
    api_url: Optional[str] = None
    api_key: Optional[str] = None
    model_id: Optional[str] = None
    llm_config: Dict = {
        "temperature": 0.0,
        "max_tokens": 512,
    }


class GenerationService:
    def __init__(self, logger: Logger):
        self.logger = logger
        self.configs: Dict[str, GenerationConfig] = {}

    def set_config(self, provider: Literal["ionos", "openai"], config: GenerationConfig):
        self.configs[provider] = config

    async def generate(self, provider: Literal["ionos", "openai"], messages: List[Dict[str, str]], model: Optional[str] = None) -> str:
        if provider not in self.configs:
            raise ValueError(f"[GenerationService] No configuration set for provider: {provider}")

        cfg = self.configs[provider]

        # Simple provider switch; actual integrations can be implemented later
        if provider == "openai":
            from langchain_core.messages import SystemMessage, HumanMessage
            from langchain_openai import ChatOpenAI

            # Build LC messages list directly and invoke the LLM
            lc_messages = []
            for m in messages:
                role = m.get("role")
                content = m.get("content", "")
                if role == "system":
                    lc_messages.append(SystemMessage(content=content))
                elif role == "user":
                    lc_messages.append(HumanMessage(content=content))

            llm = ChatOpenAI(
                model=model or (cfg.model_id or "gpt-4o-mini"),
                temperature=cfg.llm_config.get("temperature", 0.0),
                api_key=cfg.api_key,
            )
            resp = await llm.ainvoke(lc_messages)
            return (resp.content or "").strip()

        if provider == "ionos":
            # TODO: add ionos generation integration
            raise NotImplementedError("IONOS generation not implemented yet")

        raise ValueError(f"[GenerationService] Unsupported provider: {provider}")
