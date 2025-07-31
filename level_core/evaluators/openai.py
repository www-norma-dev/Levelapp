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

    def build_prompt(self, generated_text: str, expected_text: str) -> str:
        """
        Construct a human-readable scoring rubric prompt for the OpenAI model.

        Returns:
            str: Evaluation prompt text.
        """
        return f"""
        You are an expert text evaluator. Your task is to evaluate how well the agent's generated text matches the expected text using semantic similarity, factual accuracy, and completeness.

        Use this exact 6-point scale (0-5):

        5 - Perfect Match: Generated text is semantically identical to expected text. All key information, meaning, and intent are preserved with only trivial differences (punctuation, minor word order).

        4 - Excellent Match: Generated text captures all essential meaning and information with minor stylistic differences. No important details are missing or incorrect.

        3 - Good Match: Generated text covers the main points accurately but may have some minor omissions, slight inaccuracies, or different phrasing that doesn't change core meaning.

        2 - Moderate Match: Generated text captures the general idea but has noticeable differences, missing details, or minor factual errors that somewhat impact accuracy.

        1 - Poor Match: Generated text addresses the topic but has significant omissions, factual errors, or substantially different meaning from expected text.

        0 - No Match: Generated text is completely unrelated, factually incorrect, or fails to address the expected content meaningfully.

        Expected Output:
        \"\"\"
        {expected_text}
        \"\"\"

        Agent's Generated Output:
        \"\"\"
        {generated_text}
        \"\"\"

        Evaluation Instructions:
        - Focus on semantic meaning rather than exact word matching
        - Consider whether someone reading the generated text would get the same information as from the expected text
        - Penalize factual inaccuracies more heavily than stylistic differences
        - Be consistent in your scoring across similar cases

        Return your evaluation as a valid JSON object with exactly these keys:
        {{"match_level": <integer from 0 to 5>, "justification": "<brief explanation of score reasoning>"}}

        Output only the JSON object and nothing else.
        """

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
            model="gpt-4o-mini",
            temperature=0,
            api_key=self.config.api_key,
        )
        structured_llm = llm.with_structured_output(schema=EvaluationResult, method="function_calling")

        try:
            with get_openai_callback() as cb:
                chain = prompt_template | structured_llm
                response = await chain.ainvoke({})

                response.metadata = {
                    "inputTokens": cb.prompt_tokens,
                    "outputTokens": cb.completion_tokens,
                    "total_cost": cb.total_cost
                }

                return response.model_dump()

        except Exception as e:
            self.logger.error(f"[call_llm] OpenAI API request failed: {e}", exc_info=True)
        return {"error": "API request failed", "details": str(e)}
