"""
'evaluators/openai.py': OpenAI-based LLM evaluator implementation.

Uses LangChain with OpenAI's function-calling and structured output to evaluate
the quality of generated vs expected text using a predefined rubric.
"""

from typing import Union, Dict
from logging import Logger

from tenacity import retry, stop_after_attempt, wait_exponential

from langchain_community.callbacks import get_openai_callback
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from evaluators.base import BaseEvaluator
from evaluators.schemas import EvaluationConfig, EvaluationResult


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

    def build_prompt(self, generated_text: str, expected_text: str) -> str:
        """
        Construct a human-readable scoring rubric prompt for the OpenAI model.

        Returns:
            str: Evaluation prompt text.
        """
        return f"""
        Your task is to evaluate how well the generated text aligns with the expected reference.

        Use the following classification criteria:
        3 - Excellent Match: The generated text is virtually identical to the expected text with no meaningful differences.
        2 - Good Match: The generated text closely matches the expected text with only minor wording differences.
        1 - Moderate Match: The generated text captures the main ideas but has noticeable differences or omissions.
        0 - Poor Match: The generated text has significant differences and misses several key points.

        Reference Text:
        \"\"\"
        {expected_text}
        \"\"\"

        Generated Text:
        \"\"\"
        {generated_text}
        \"\"\"

        Return your evaluation as a valid JSON object with exactly these keys:
        {{
            "match_level": <an integer between 0 and 3>,  ## scale clarified and generalized
            "justification": <a brief explanation>
        }}

        Output only the JSON object and nothing else.
        """  ## renamed Agent/Expected Output ~ Generated/Reference Text for generalization

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def call_llm(self, prompt: str) -> Union[Dict, str]:
        """
        Send evaluation prompt to OpenAI via LangChain with structured function-calling.

        Args:
            prompt (str): The full scoring prompt.

        Returns:
            Union[Dict, str]: A dictionary containing match_level, justification, and token metadata.
                              Returns a string on failure.
        """
        messages = [
            self.SystemMessage(content="You are an evaluation assistant."),
            self.HumanMessage(content=prompt)
        ]
        prompt_template = self.ChatPromptTemplate.from_messages(messages=messages)

        llm = self.ChatOpenAI(
            model=self.config.model_id or "gpt-4o-mini",  ## fallback to default model if not provided
            temperature=self.config.llm_config.get("temperature", 0),
            api_key=self.config.api_key,
        )

        structured_llm = llm.with_structured_output(schema=EvaluationResult, method="function_calling")

        try:
            with get_openai_callback() as cb:
                chain = prompt_template | structured_llm
                response = await chain.ainvoke({})

                ## generalized metadata keys to use snake_case
                response.metadata = {
                    "input_tokens": cb.prompt_tokens,
                    "output_tokens": cb.completion_tokens,
                    "total_cost": cb.total_cost
                }

                return response.model_dump()

        except Exception as e:
            self.logger.error(f"[call_llm] OpenAI API request failed: {e}", exc_info=True)
            return {"error": "API request failed", "details": str(e)}
