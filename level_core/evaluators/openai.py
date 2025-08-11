"""
'evaluators/openai.py': OpenAI-based LLM evaluator implementation.

Uses LangChain with OpenAI's function-calling and structured output to evaluate
the quality of generated vs expected text using a predefined rubric.
"""
from typing import Union, Dict, Optional
from logging import Logger

from tenacity import retry, stop_after_attempt, wait_exponential

from langchain_community.callbacks import get_openai_callback
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from .base import BaseEvaluator
from .schemas import EvaluationConfig, EvaluationResult


class OpenAIEvaluator(BaseEvaluator):
    """Evaluator that uses OpenAI's GPT models via LangChain for structured evaluation."""
    def __init__(self, config: EvaluationConfig, logger: Logger):
        """
        Args:
            config (EvaluationConfig): Configuration for the LLM and API.
            logger (Logger): Logger for error/debug reporting.
        """
        super().__init__(config, logger)
        self.SystemMessage = SystemMessage
        self.HumanMessage = HumanMessage
        self.ChatPromptTemplate = ChatPromptTemplate
        self.ChatOpenAI = ChatOpenAI

    def build_prompt(self, user_message: Optional[str], generated_text: str, expected_text: str) -> str:
        """Simplified evaluation prompt (heuristic key points handled outside)."""
        user_msg = user_message or "(no user message provided)"
        parts = [
            "You are an expert text evaluator. Score generated vs expected for semantic similarity, factual accuracy, completeness.",
            "Provide only JSON: {\"match_level\": <0-5>, \"justification\": \"<<=35 words reason>\", \"metadata\": {}}",
            "Scale: 5 perfect; 4 excellent; 3 good; 2 moderate gaps; 1 poor; 0 no match/incorrect.",
            "",
            "User Message:", '"""', user_msg, '"""',
            "",
            "Expected:", '"""', expected_text, '"""',
            "",
            "Generated:", '"""', generated_text, '"""',
        ]
        return "\n".join(parts)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def call_llm(self, prompt: str) -> Union[Dict, str]:
        """Send evaluation prompt and return structured result with token + key point metadata."""
        try:
            messages = [
                self.SystemMessage(content="You are an evaluation assistant."),
                self.HumanMessage(content=prompt)
            ]
            prompt_template = self.ChatPromptTemplate.from_messages(messages=messages)

            llm = self.ChatOpenAI(model="gpt-4o-mini", temperature=0)
            with get_openai_callback() as cb:
                chain = prompt_template | llm
                raw = await chain.ainvoke({})
                # Fallback heuristic: we expect model text output containing JSON
                content = getattr(raw, 'content', '') if raw else ''
                parsed = self._parse_json_output(content) if content else {}
                meta = {
                    "inputTokens": cb.prompt_tokens,
                    "outputTokens": cb.completion_tokens,
                    "total_cost": cb.total_cost,
                }
                if isinstance(parsed, dict):
                    parsed.setdefault("metadata", {})
                    if isinstance(parsed["metadata"], dict):
                        parsed["metadata"].update(meta)
                else:
                    parsed = {"match_level": 0, "justification": "Non-JSON output", "metadata": meta}
                return parsed
        except Exception as ex:
            self.logger.error(f"[call_llm] OpenAI API request failed: {ex}", exc_info=True)
            return {"error": "API request failed", "details": str(ex)}
