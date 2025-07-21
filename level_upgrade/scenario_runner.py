"""
ScenarioRunner class for orchestrating the complete chatbot evaluation workflow.
This is the main class that ties together chat simulation, evaluation, and export.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from level_core.evaluators.service import EvaluationService
from level_core.evaluators.schemas import EvaluationConfig
from level_core.evaluators.ionos import IonosEvaluator
from level_core.evaluators.openai import OpenAIEvaluator

from .config import Config
from .chat_simulator import ChatSimulator
from .evaluators.local_evaluator import LocalEvaluator
from .exporters.results_exporter import ResultsExporter

logger = logging.getLogger(__name__)

class ScenarioRunner:
    """Main orchestration class for chatbot evaluation scenarios."""
    
    def __init__(self, config: Config = None):
        """
        Initialize ScenarioRunner with configuration.
        
        Args:
            config: Configuration object (creates default if None)
        """
        self.config = config or Config.from_env()
        self.logger = logger
        
        # Initialize components
        self.chat_simulator = ChatSimulator(self.config)
        self.results_exporter = ResultsExporter(self.config)
        
        # Evaluation service (initialized when needed)
        self.evaluation_service = None
    
    def _setup_evaluation_service(self, evaluator_type: str = "local"):
        """
        Set up the evaluation service with the specified evaluator type.
        
        Args:
            evaluator_type: Type of evaluator ("local", "ionos", "openai")
        """
        self.evaluation_service = EvaluationService(self.logger)
        
        if evaluator_type == "local":
            self.evaluation_service.register_evaluator("local", LocalEvaluator)
            config = EvaluationConfig(
                api_url=self.config.evaluator_api_url,
                model_id=self.config.evaluator_model_id,
                llm_config=self.config.llm_config
            )
            self.evaluation_service.set_config("local", config)
            
        elif evaluator_type == "ionos":
            self.evaluation_service.register_evaluator("ionos", IonosEvaluator)
            config = EvaluationConfig(
                api_url=self.config.evaluator_api_url,
                api_key=self.config.evaluator_api_key,
                model_id=self.config.evaluator_model_id,
                llm_config=self.config.llm_config
            )
            self.evaluation_service.set_config("ionos", config)
            
        elif evaluator_type == "openai":
            self.evaluation_service.register_evaluator("openai", OpenAIEvaluator)
            config = EvaluationConfig(
                api_url=self.config.openai_api_url,
                api_key=self.config.openai_api_key,
                model_id=self.config.openai_model_id,
                llm_config=self.config.llm_config
            )
            self.evaluation_service.set_config("openai", config)
        
        else:
            raise ValueError(f"Unsupported evaluator type: {evaluator_type}")
    
    async def evaluate_conversation(
        self,
        prompts: List[str], 
        replies: List[str],
        evaluator_type: str = "local"
    ) -> Dict[str, Any]:
        """
        Evaluate a chatbot conversation using LLM-as-judge approach.
        
        Args:
            prompts: List of user prompts
            replies: List of chatbot replies
            evaluator_type: Type of evaluator to use
            
        Returns:
            Comprehensive evaluation results
        """
        if len(prompts) != len(replies):
            raise ValueError("Number of prompts and replies must match")
        
        # Set up evaluation service if not already done
        if not self.evaluation_service:
            self._setup_evaluation_service(evaluator_type)
        
        # Evaluate each prompt-reply pair
        evaluation_results = []
        total_score = 0
        score_counts = {0: 0, 1: 0, 2: 0, 3: 0}
        
        self.logger.info(f"Evaluating {len(prompts)} conversation turns using {evaluator_type} evaluator")
        print(f"\n🔍 Evaluating {len(prompts)} conversation turns using {evaluator_type} evaluator...")
        
        for i, (prompt, reply) in enumerate(zip(prompts, replies), 1):
            print(f"Evaluating turn {i}/{len(prompts)}...")
            
            try:
                # Use the evaluator
                result = await self.evaluation_service.evaluate_response(
                    provider=evaluator_type,
                    output_text=reply,
                    reference_text=prompt
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
                self.logger.error(f"Error evaluating turn {i}: {e}")
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
                "model_used": self.config.evaluator_model_id
            }
        }
    
    def print_evaluation_report(self, evaluation_results: Dict[str, Any]):
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
    
    async def run_complete_scenario(
        self,
        prompts: List[str] = None,
        rag_url: str = None,
        evaluator_type: str = "local",
        scenario_name: str = None,
        export_results: bool = True
    ) -> Dict[str, Any]:
        """
        Run a complete evaluation scenario from start to finish.
        
        Args:
            prompts: List of prompts to use (uses example if None)
            rag_url: URL for RAG initialization
            evaluator_type: Type of evaluator to use
            scenario_name: Name for exported results
            export_results: Whether to export results to JSON
            
        Returns:
            Complete scenario results including file paths
        """
        print("🚀 Level Upgrade: Complete Evaluation Scenario")
        print("=" * 60)
        
        # Show configuration
        self.config.print_config()
        
        # Use example prompts if none provided
        if not prompts:
            prompts = [
                "Hello, how are you?",
                "What's the weather like?",
                "Tell me a joke",
                "What's 2+2?",
                "Goodbye!"
            ]
        
        try:
            # Step 1: Initialize RAG if URL provided
            if rag_url:
                print(f"\n🔧 Initializing RAG with: {rag_url}")
                init_result = await self.chat_simulator.init_rag(rag_url)
                print(f"RAG Init Result: {init_result}")
            
            # Step 2: Run chat simulation
            print("\n🤖 Running Chat Simulation...")
            replies = await self.chat_simulator.simulate_conversation(prompts)
            self.chat_simulator.print_conversation(prompts, replies)
            
            # Step 3: Evaluate conversation
            print(f"\n🔍 Starting LLM-as-Judge Evaluation...")
            evaluation_results = await self.evaluate_conversation(
                prompts, replies, evaluator_type
            )
            
            # Step 4: Print evaluation report
            self.print_evaluation_report(evaluation_results)
            
            # Step 5: Export results if requested
            result_files = {}
            if export_results:
                print("\n💾 Exporting results...")
                
                # JSON export
                json_file = self.results_exporter.save_scenario_results(
                    evaluation_results,
                    rag_url=rag_url,
                    scenario_name=scenario_name
                )
                result_files["json"] = json_file
                
                # Preview JSON structure
                scenario_json = self.results_exporter.export_scenario_to_json(
                    evaluation_results, rag_url
                )
                self.results_exporter.print_json_preview(scenario_json)
                
                print(f"✅ Results exported successfully!")
            
            # Return complete results
            return {
                "scenario_metadata": {
                    "rag_url": rag_url,
                    "evaluator_type": evaluator_type,
                    "scenario_name": scenario_name,
                    "exported_files": result_files
                },
                "conversation": {
                    "prompts": prompts,
                    "replies": replies
                },
                "evaluation_results": evaluation_results,
                "summary_stats": self.results_exporter.get_summary_stats(evaluation_results)
            }
            
        except Exception as e:
            self.logger.error(f"Error in complete scenario: {e}")
            print(f"\n❌ Error running scenario: {e}")
            raise
    
    async def run_example_scenario(self) -> Dict[str, Any]:
        """
        Run an example scenario for demonstration purposes.
        
        Returns:
            Complete scenario results
        """
        return await self.run_complete_scenario(
            rag_url="https://www.ionos.com",
            scenario_name="example_ionos_evaluation"
        ) 