"""
LocalEvaluator class for evaluating chatbot responses using local Llama models.
Extends the BaseEvaluator from level_core to work with local API format.
"""

import logging
from typing import Dict, Any
from level_core.evaluators.base import BaseEvaluator
from level_core.evaluators.schemas import EvaluationConfig
from level_core.simluators.utils import async_request
from ..config import Config

logger = logging.getLogger(__name__)

class LocalEvaluator(BaseEvaluator):
    """Custom evaluator that works with local Llama API format."""
    
    def __init__(self, config: EvaluationConfig, level_config: Config = None):
        """
        Initialize LocalEvaluator.
        
        Args:
            config: EvaluationConfig for the evaluator
            level_config: Level Upgrade Config object (optional)
        """
        super().__init__(config)
        self.level_config = level_config
        self.logger = logger
    
    def build_prompt(self, generated_text: str, expected_text: str) -> str:
        """
        Build evaluation prompt for chatbot response quality assessment.
        
        Args:
            generated_text: The chatbot's response to evaluate
            expected_text: The original user prompt (used as context)
            
        Returns:
            Evaluation prompt for the LLM judge
        """
        return f"""You are an expert evaluator of conversational AI systems. Your task is to evaluate the quality of a chatbot's response to a user prompt.

Evaluation Criteria:
- Relevance: How well does the response address the user's prompt?
- Helpfulness: Is the response useful and informative?
- Clarity: Is the response clear and easy to understand?
- Appropriateness: Is the tone and style appropriate for the conversation?
- Accuracy: Is the information provided correct (if factual claims are made)?

Rating Scale:
3 - Excellent: Response is highly relevant, helpful, clear, appropriate, and accurate
2 - Good: Response is mostly relevant and helpful with minor issues
1 - Fair: Response addresses the prompt but has notable deficiencies
0 - Poor: Response is irrelevant, unhelpful, unclear, or inappropriate

User Prompt:
"{expected_text}"

Chatbot Response:
"{generated_text}"

Evaluate this chatbot response and return your assessment as a valid JSON object with exactly these keys:
{{
    "match_level": <integer 0-3>,
    "justification": "<brief explanation of your rating with specific strengths/weaknesses>"
}}

Output only the JSON object and nothing else."""

    async def call_llm(self, prompt: str) -> Dict:
        """
        Call the local Llama model for evaluation using the same format as chat simulation.
        
        Args:
            prompt: The evaluation prompt
            
        Returns:
            Parsed evaluation result or error dict
        """
        # Use level_config if available, otherwise fall back to self.config
        if self.level_config:
            api_base_url = self.level_config.evaluator_api_url
            model_id = self.level_config.evaluator_model_id
        else:
            api_base_url = self.config.api_url
            model_id = self.config.model_id
        
        try:
            response = await async_request(
                url=api_base_url,
                headers={
                    "Content-Type": "application/json",
                    "x-model-id": model_id
                },
                payload={
                    "prompt": prompt,
                }
            )
            
            if response and response.status_code == 200:
                try:
                    response_data = response.json()
                    
                    # Extract the response text (same logic as chat_simulation)
                    if isinstance(response_data, str):
                        output = response_data
                    elif isinstance(response_data, dict):
                        output = (response_data.get("response") or 
                                response_data.get("text") or 
                                response_data.get("content") or 
                                response_data.get("message") or 
                                response_data.get("output") or
                                str(response_data))
                    else:
                        output = str(response_data)
                    
                    # Parse the JSON output from the LLM
                    parsed_output = self._parse_json_output(output)
                    
                    # Add metadata
                    if "metadata" not in parsed_output:
                        parsed_output["metadata"] = {}
                    parsed_output["metadata"].update({
                        "model_used": model_id,
                        "evaluator": "LocalEvaluator",
                        "api_url": api_base_url
                    })
                    
                    return parsed_output
                    
                except Exception as e:
                    self.logger.error(f"Error parsing evaluation response: {e}")
                    return {"error": "Response parsing failed", "details": str(e)}
            else:
                status_code = response.status_code if response else "No response"
                self.logger.error(f"API request failed with status: {status_code}")
                return {"error": "API request failed", "status_code": status_code}
                
        except Exception as e:
            self.logger.error(f"LLM evaluation call failed: {e}")
            return {"error": "LLM call failed", "details": str(e)}

    @classmethod
    def from_level_config(cls, level_config: Config) -> "LocalEvaluator":
        """
        Create LocalEvaluator from Level Upgrade Config.
        
        Args:
            level_config: Level Upgrade configuration
            
        Returns:
            Configured LocalEvaluator instance
        """
        eval_config = EvaluationConfig(
            api_url=level_config.evaluator_api_url,
            model_id=level_config.evaluator_model_id,
            llm_config=level_config.llm_config
        )
        
        return cls(eval_config, level_config) 