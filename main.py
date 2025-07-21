import json
import asyncio
import os
from typing import List, Dict, Any, Optional
from level_core.simluators.utils import async_request
from level_core.evaluators.service import EvaluationService
from level_core.evaluators.schemas import EvaluationConfig, EvaluationResult
from level_core.evaluators.base import BaseEvaluator
from level_core.evaluators.ionos import IonosEvaluator
from level_core.evaluators.openai import OpenAIEvaluator
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LocalEvaluator(BaseEvaluator):
    """Custom evaluator that works with local Llama API format."""
    
    def build_prompt(self, generated_text: str, expected_text: str) -> str:
        """Build evaluation prompt for chatbot response quality assessment."""
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
        """Call the local Llama model for evaluation using the same format as chat_simulation."""
        api_base_url = os.getenv("EVALUATOR_API_URL", os.getenv("API_BASE_URL", "http://127.0.0.1:8000"))
        model_id = os.getenv("EVALUATOR_MODEL_ID", os.getenv("MODEL_ID", "meta-llama/Llama-3.3-70B-Instruct"))
        
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
                    logger.error(f"Error parsing evaluation response: {e}")
                    return {"error": "Response parsing failed", "details": str(e)}
            else:
                status_code = response.status_code if response else "No response"
                logger.error(f"API request failed with status: {status_code}")
                return {"error": "API request failed", "status_code": status_code}
                
        except Exception as e:
            logger.error(f"LLM evaluation call failed: {e}")
            return {"error": "LLM call failed", "details": str(e)}

async def evaluate_chatbot_conversation(
    prompts: List[str], 
    replies: List[str],
    evaluator_type: str = "local"
) -> Dict[str, Any]:
    """
    Evaluate a chatbot conversation using existing LLM evaluators.
    
    Args:
        prompts: List of user prompts
        replies: List of chatbot replies
        evaluator_type: Type of evaluator to use ("local", "ionos", "openai")
        
    Returns:
        Comprehensive evaluation results
    """
    if len(prompts) != len(replies):
        raise ValueError("Number of prompts and replies must match")
    
    # Initialize evaluation service
    evaluation_service = EvaluationService(logger)
    
    # Register and configure evaluator based on type
    if evaluator_type == "local":
        evaluation_service.register_evaluator("local", LocalEvaluator)
        config = EvaluationConfig(
            api_url=os.getenv("EVALUATOR_API_URL", os.getenv("API_BASE_URL", "http://127.0.0.1:8000")),
            model_id=os.getenv("EVALUATOR_MODEL_ID", os.getenv("MODEL_ID", "meta-llama/Llama-3.3-70B-Instruct")),
            llm_config={
                "temperature": 0.1,  # Low temperature for consistent evaluation
                "max_tokens": 200
            }
        )
        evaluation_service.set_config("local", config)
        
    elif evaluator_type == "ionos":
        evaluation_service.register_evaluator("ionos", IonosEvaluator)
        config = EvaluationConfig(
            api_url=os.getenv("EVALUATOR_API_URL", os.getenv("API_BASE_URL", "http://127.0.0.1:8000")),
            api_key=os.getenv("EVALUATOR_API_KEY", "dummy-key"),  # Local API might not need real key
            model_id=os.getenv("EVALUATOR_MODEL_ID", os.getenv("MODEL_ID", "meta-llama/Llama-3.3-70B-Instruct")),
            llm_config={
                "temperature": 0.1,  # Low temperature for consistent evaluation
                "max_tokens": 200
            }
        )
        evaluation_service.set_config("ionos", config)
        
    elif evaluator_type == "openai":
        evaluation_service.register_evaluator("openai", OpenAIEvaluator)
        config = EvaluationConfig(
            api_url=os.getenv("OPENAI_API_URL", "https://api.openai.com/v1/chat/completions"),
            api_key=os.getenv("OPENAI_API_KEY"),
            model_id=os.getenv("OPENAI_MODEL_ID", "gpt-4o-mini"),
            llm_config={
                "temperature": 0.1,
                "max_tokens": 200
            }
        )
        evaluation_service.set_config("openai", config)
    
    # Evaluate each prompt-reply pair
    evaluation_results = []
    total_score = 0
    score_counts = {0: 0, 1: 0, 2: 0, 3: 0}
    
    print(f"\n🔍 Evaluating {len(prompts)} conversation turns using {evaluator_type} evaluator...")
    
    for i, (prompt, reply) in enumerate(zip(prompts, replies), 1):
        print(f"Evaluating turn {i}/{len(prompts)}...")
        
        try:
            # Use the evaluator - pass reply as output_text and prompt as reference_text
            result = await evaluation_service.evaluate_response(
                provider=evaluator_type,
                output_text=reply,
                reference_text=prompt  # Using prompt as reference for context
            )
            
            if result and hasattr(result, 'match_level'):
                score = result.match_level
                total_score += score
                score_counts[score] += 1
                
                evaluation_results.append({
                    "turn": i,
                    "user_prompt": prompt,
                    "bot_reply": reply,
                    "evaluation_score": score,
                    "justification": result.justification,
                    "metadata": getattr(result, 'metadata', {}),
                    "status": "success"
                })
            else:
                evaluation_results.append({
                    "turn": i,
                    "user_prompt": prompt,
                    "bot_reply": reply,
                    "evaluation_score": 0,
                    "justification": "Evaluation failed",
                    "metadata": {},
                    "status": "error"
                })
                
        except Exception as e:
            logger.error(f"Error evaluating turn {i}: {e}")
            evaluation_results.append({
                "turn": i,
                "user_prompt": prompt,
                "bot_reply": reply,
                "evaluation_score": 0,
                "justification": f"Evaluation error: {str(e)}",
                "metadata": {},
                "status": "error"
            })
    
    # Calculate summary statistics
    avg_score = total_score / len(prompts) if prompts else 0
    
    summary = {
        "total_turns": len(prompts),
        "average_score": round(avg_score, 2),
        "score_distribution": score_counts,
        "excellent_responses": score_counts[3],
        "good_responses": score_counts[2],
        "fair_responses": score_counts[1],
        "poor_responses": score_counts[0],
        "success_rate": round((sum(score_counts.values()) - score_counts[0]) / len(prompts) * 100, 1) if prompts else 0
    }
    
    return {
        "summary": summary,
        "detailed_results": evaluation_results,
        "evaluation_metadata": {
            "evaluator_type": evaluator_type,
            "timestamp": asyncio.get_event_loop().time(),
            "model_used": os.getenv("EVALUATOR_MODEL_ID", os.getenv("MODEL_ID", "meta-llama/Llama-3.3-70B-Instruct"))
        }
    }

def print_evaluation_report(evaluation_results: Dict[str, Any]):
    """Print a formatted evaluation report."""
    summary = evaluation_results["summary"]
    detailed = evaluation_results["detailed_results"]
    
    print("\n" + "="*60)
    print("🎯 CHATBOT EVALUATION REPORT")
    print("="*60)
    
    print(f"\n📊 SUMMARY STATISTICS:")
    print(f"   Total Conversation Turns: {summary['total_turns']}")
    print(f"   Average Score: {summary['average_score']}/3.0")
    print(f"   Success Rate: {summary['success_rate']}%")
    
    print(f"\n📈 SCORE DISTRIBUTION:")
    print(f"   🌟 Excellent (3): {summary['excellent_responses']} responses")
    print(f"   ✅ Good (2): {summary['good_responses']} responses") 
    print(f"   ⚠️  Fair (1): {summary['fair_responses']} responses")
    print(f"   ❌ Poor (0): {summary['poor_responses']} responses")
    
    print(f"\n📝 DETAILED RESULTS:")
    for result in detailed:
        status_icon = "✅" if result["status"] == "success" else "❌"
        score_icon = ["❌", "⚠️", "✅", "🌟"][result["evaluation_score"]]
        
        print(f"\n{status_icon} Turn {result['turn']} {score_icon} Score: {result['evaluation_score']}/3")
        print(f"   User: {result['user_prompt']}")
        print(f"   Bot:  {result['bot_reply']}")
        print(f"   Judge: {result['justification']}")

async def init_rag(url: str):
    response = await async_request(
        url= "http://127.0.0.1:8000/init",
        headers={"Content-Type": "application/json"},
        payload={
            f"page_url": url,
        }
    )
    if response and response.status_code == 200:
        try:
            return response.json()
        except:
            return {"status": "success", "message": response.text}
    return {"status": "error", "message": "Failed to initialize RAG"}

async def chat_simulation(prompts: List[str], model_id: Optional[str] = None) -> List[str]:
    """
    Simulate a conversation by processing a list of user prompts sequentially.
    
    Args:
        prompts: List of user prompts to process
        model_id: Model ID to use (defaults to environment variable)
        
    Returns:
        List of chatbot replies in the same order as input prompts
    """
    # Get model ID from environment or parameter
    if not model_id:
        model_id = os.getenv("MODEL_ID", "meta-llama/Llama-3.3-70B-Instruct")
    
    # Get API base URL from environment
    api_base_url = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
    
    replies = []
    
    for prompt in prompts:
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
                    # Try to parse as JSON first
                    response_data = response.json()
                    
                    # Handle different possible response formats
                    if isinstance(response_data, str):
                        # Simple string response
                        reply = response_data
                    elif isinstance(response_data, dict):
                        # Dictionary response - try common keys
                        reply = (response_data.get("response") or 
                                response_data.get("text") or 
                                response_data.get("content") or 
                                response_data.get("message") or 
                                response_data.get("output") or
                                str(response_data))
                    else:
                        reply = str(response_data)
                        
                    replies.append(reply.strip() if isinstance(reply, str) else str(reply))
                    
                except json.JSONDecodeError:
                    # If JSON parsing fails, use raw text
                    reply = response.text.strip()
                    replies.append(reply if reply else "No response generated")
                    
            else:
                # Handle failed requests
                error_msg = f"Request failed with status: {response.status_code if response else 'No response'}"
                replies.append(f"Error: {error_msg}")
                
        except Exception as e:
            # Handle any unexpected errors
            replies.append(f"Error processing prompt: {str(e)}")
    
    return replies

# Example usage functions
async def example_basic_simulation():
    """Example of basic chat simulation without context."""
    prompts = [
        "Hello, how are you?",
        "What's the weather like?",
        "Tell me a joke",
        "What's 2+2?",
        "Goodbye!"
    ]
    
    print("🤖 Running Basic Chat Simulation...")
    replies = await chat_simulation(prompts)
    
    print("\n📝 Results:")
    for i, (prompt, reply) in enumerate(zip(prompts, replies), 1):
        print(f"\nTurn {i}:")
        print(f"  User: {prompt}")
        print(f"  Bot:  {reply}")
    
    return prompts, replies

async def main():
    """Main function to demonstrate the chat simulation functions."""
    print("🚀 Level Core Chat Simulation Demo")
    print("=" * 50)
    
    # Show environment configuration
    print(f"📡 API Base URL: {os.getenv('API_BASE_URL', 'http://127.0.0.1:8000')}")
    print(f"🤖 Model ID: {os.getenv('MODEL_ID', 'meta-llama/Llama-3.3-70B-Instruct')}")
    
    try:
        print("\n🔧 Initializing RAG...")
        init_result = await init_rag("https://www.ionos.com")
        print(f"RAG Init Result: {init_result}")
        
        # Run basic simulation example
        prompts, replies = await example_basic_simulation()
        
        # Evaluate the conversation using local evaluator
        print("\n🔍 Starting LLM-as-Judge Evaluation...")
        evaluation_results = await evaluate_chatbot_conversation(
            prompts, 
            replies, 
            evaluator_type="local"  # Use the custom LocalEvaluator
        )
        
        # Print the evaluation report
        print_evaluation_report(evaluation_results)
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        print("💡 Make sure your local API server is running on the configured port!")

if __name__ == "__main__":
    asyncio.run(main())