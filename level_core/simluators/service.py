"""
levelapp_core_simulators/service.py: Generic service layer for conversation simulation and evaluation.
"""
import asyncio
import time
from typing import Dict, Any, List, Callable, Optional
from collections import defaultdict
from datetime import datetime
from .schemas import InteractionEvaluationResult, Interaction, BasicConversation, ConversationBatch
from .utils import (
    extract_interaction_details,
    async_request,
    parse_date_value,
    calculate_average,
    summarize_justifications,
    calculate_handoff_stats,
)
from .event_collector import add_event
from level_core.simluators.schemas import ConversationBatch
from level_core.evaluators.service import EvaluationService
from level_core.evaluators.utils import evaluate_metadata
class ConversationSimulator:
    """
    Generic service to simulate conversations and evaluate interactions.
    """
    def __init__(self, batch: ConversationBatch, evaluation_service: EvaluationService, persistence_fn: Optional[Callable] = None):
        """
        Initialize the ConversationSimulator.

        Args:
            batch (ConversationBatch): The batch of scenarios to simulate (user supplies structure).
            evaluation_fn (Callable): Function to evaluate interactions (user supplies).
            persistence_fn (Callable): Function to persist results (user supplies).
        """
        self.batch = batch
        self.evaluation_service = evaluation_service  # User-supplied evaluation logic
        self.persistence_fn = persistence_fn  # User-supplied persistence logic
        self.collected_scores = defaultdict(list)
        self.evaluation_summaries = defaultdict(list)
        self.execution_events = []  # Collect execution events instead of logging


    def setup_simulator(self, endpoint: str, headers: Dict[str, str]):
        """
        Set up the simulator with endpoint and headers.

        Args:
            endpoint (str): The endpoint URL for the simulator.
            headers (Dict[str, str]): HTTP headers for requests.
        """
        self.endpoint = endpoint
        self.headers = headers

    async def run_batch_test(self, name: str, test_load: Dict[str, Any], attempts: int = 1) -> Dict[str, Any]:
        """
        Run a batch test for the given batch name and details.

        Args:
            name (str): The name of the batch test.
            test_load (Dict[str, Any]): The test load configuration.
            attempts (int, optional): Number of attempts to run. Defaults to 1.

        Returns:
            Dict[str, Any]: The test results with status information.
        """
        add_event("INFO", f"Starting batch test for batch: {name}")
        # started_at = datetime.now().isoformat()
        # start_time = time.time()
        results = await self.simulate_conversation(attempts=attempts)
        # finished_at = datetime.now().isoformat()
        # elapsed_time = time.time() - start_time
        # average_execution_time = calculate_average(results["scenarios"])
        # test_load["results"] = {
        #     "started_at": started_at,
        #     "finished_at": finished_at,
        #     "total_duration_seconds": elapsed_time,
        #     "global_justification": self.evaluation_summaries,
        #     "average_scores": results["average_scores"],
        #     "scenarios": results["scenarios"],
        #     "average_execution_time": average_execution_time,
        #     "execution_events": self.execution_events,  # (Legacy) - consider using event_collector.execution_events
        # }
        # if self.persistence_fn:
        #     self.persistence_fn(test_load)
        return results

    async def simulate_conversation(self, attempts: int = 1) -> Dict[str, Any]:
        """
        Simulate conversations for all scenarios in the batch.

        Args:
            attempts (int, optional): Number of attempts per scenario. Defaults to 1.

        Returns:
            Dict[str, Any]: The simulation results with scenarios and average scores.
        """
        add_event("INFO", "Starting conversation simulation..")
        semaphore = asyncio.Semaphore(value=len(self.batch.conversations))
        async def run_with_semaphore(scenario: Any) -> Dict[str, Any]:
            async with semaphore:
                return await self.simulate_single_scenario(scenario=scenario, attempts=attempts)
        results = await asyncio.gather(*(run_with_semaphore(s) for s in self.batch.conversations))
        aggregate_scores: Dict[str, List[float]] = defaultdict(list)
        for scenarios_results in results:
            for key, value in scenarios_results.get("averageScores", {}).items():
                if isinstance(value, (int, float)):
                    aggregate_scores[key].append(value)
        overall_average_scores = calculate_average(aggregate_scores)
        for provider, justifications in self.evaluation_summaries.items():
            self.evaluation_summaries[provider] = summarize_justifications(
                justifications=justifications
            )
        # all_handoff_vals: List[float] = []
        # for scen in results:
        #     for attempt in scen.get("attempts", []):
        #         val = attempt.get("handoffPassAverage")
        #         if isinstance(val, (int, float)):
        #             all_handoff_vals.append(val)
        # handoff_avg_map = calculate_average({"handoff": all_handoff_vals})
        # overall_average_scores["handoff"] = handoff_avg_map.get("handoff", 0.0)
        return {
            "scenarios": results,
            "average_scores": overall_average_scores,
        }

    async def simulate_single_scenario(self, scenario: BasicConversation, attempts: int = 1) -> Dict[str, Any]:
        """
        Simulate a single scenario with the given number of attempts.

        Args:
            scenario (BasicConversation): The scenario to simulate.
            attempts (int, optional): Number of attempts to run. Defaults to 1.

        Returns:
            Dict[str, Any]: The simulation results for the single scenario.
        """
        scenario_id = scenario.id
        add_event("INFO", f"Starting simulation for scenario: {scenario_id}")
        attempt_results = []
        all_attempts_scores = defaultdict(list)
        for attempt in range(attempts):
            add_event("INFO", f"Running attempt: {attempt+1}/{attempts}", {"scenario_id": scenario_id})
            start_time = time.time()
            self.collected_scores = defaultdict(list)
            # attempt_handoff_checks: List[int] = []
            conversation_id = f"batch-{attempt+1}"
            # initial_interaction_results = await self.simulate_initial_interaction(
            #     scenario=scenario,
            #     conversation_id=conversation_id
            # )
            # attempt_handoff_checks.append(initial_interaction_results.get("handoffPassCheck", 0))
            interactions_results = await self.simulate__interactions(
                scenario=scenario,
                conversation_id=conversation_id
            )
            # for r in inbound_interactions_results:
                # if "handoffPassCheck" in r:
                #     attempt_handoff_checks.append(r["handoffPassCheck"])
                # pass 
            single_attempt_scores = calculate_average(self.collected_scores)
            for key in all_attempts_scores:
                all_attempts_scores[key].append(single_attempt_scores)
            # elapsed_time = time.time() - start_time
            # handoff_stats = calculate_handoff_stats(attempt_handoff_checks)
            # attempt_handoff_average = handoff_stats["average"]
            # all_attempts_scores["handoff"].append(attempt_handoff_average)
            attempt_results.append({
                "attempt_id": attempt + 1,
                "conversation_id": conversation_id,
                "interactions": interactions_results,  # renamed from inbound_interactions
                "average_scores": single_attempt_scores,
                "execution_time": f"{time.time() - start_time:.2f}",
            })
        average_scores = calculate_average(all_attempts_scores)

        return {
            "scenario_id": scenario_id,
            "attempts": attempt_results,
            "average_scores": average_scores,
        }

    # async def simulate_initial_interaction(self, scenario: Any, conversation_id: str) -> Dict[str, Any]:
    #     """
    #     Simulate the initial interaction for a scenario.

    #     Args:
    #         scenario (Any): The scenario to simulate.
    #         conversation_id (str): The conversation ID.

    #     Returns:
    #         Dict[str, Any]: The results of the initial interaction simulation.
    #     """
    #     add_event("INFO", "Starting initial interaction simulation..")
    #     start_time = time.time()
    #     initial_interaction = getattr(scenario, 'initial_interaction', None)
    #     if initial_interaction is None:
    #         return {}
    #     initial_interaction.conversation_id = conversation_id
    #     expected_metadata = getattr(scenario, 'expected_metadata', {})
    #     # User must supply serialization logic for their scenario objects
    #     payload = getattr(initial_interaction, 'to_dict', lambda: dict())()
    #     response = await async_request(
    #         url=self.endpoint,
    #         headers=self.headers,
    #         payload=payload,
    #     )
    #     if not response or not response.status_code == 200:
    #         add_event("ERROR", "Initial interaction request failed.", {
    #             "status_code": response.status_code if response else "No response",
    #             "conversation_id": conversation_id
    #         })
    #         return {
    #             "userMessage": getattr(initial_interaction, 'message', None),
    #             "reply": "Request failed",
    #             "expectedReply": getattr(scenario, 'expected_initial_reply', None),
    #             "extractedMetadata": {},
    #             "expectedMetadata": expected_metadata,
    #             "handoffDetails": None,
    #             "interactionType": "",
    #             "evaluationResults": {},
    #             "handoffPassCheck": 0,
    #         }
    #     interaction_details = extract_interaction_details(response_text=response.text)
    #     evaluation_results = None
    #     if self.evaluation_fn:
    #         evaluation_results = self.evaluation_fn(
    #             extracted_reply=interaction_details.reply,
    #             reference_reply=getattr(scenario, 'expected_initial_reply', None),
    #             extracted_metadata=interaction_details.extracted_metadata,
    #             reference_metadata=expected_metadata,
    #             scenario_id=getattr(scenario, 'scenario_id', 'unknown')
    #         )
    #     # actual_handoff = interaction_details.handoff_details is not None
    #     # expected_handoff = getattr(initial_interaction, 'expected_handoff_pass', False)
    #     # handoff_pass_check = 1 if expected_handoff == actual_handoff else 0
    #     elapsed_time = time.time() - start_time
    #     return {
    #         "userMessage": getattr(initial_interaction, 'message', None),
    #         "reply": interaction_details.reply,
    #         "expectedReply": getattr(scenario, 'expected_initial_reply', None),
    #         "extractedMetadata": interaction_details.extracted_metadata,
    #         "expectedMetadata": expected_metadata,
    #         "handoffDetails": interaction_details.handoff_details,
    #         "interactionType": interaction_details.interaction_type,
    #         "evaluationResults": evaluation_results,
    #         "handoffPassCheck": 0, # Commented out handoff logic
    #         "executionTime": f"{elapsed_time:.2f}",
    #     }

    async def simulate__interactions(self, scenario: BasicConversation, conversation_id: str) -> List[Dict[str, Any]]:
        """
        Simulate inbound interactions for a scenario.

        Args:
            scenario (BasicConversation): The scenario to simulate.
            conversation_id (str): The conversation ID.

        Returns:
            List[Dict[str, Any]]: The results of the inbound interactions simulation.
        """
        add_event("INFO", "Starting inbound interactions simulation..")
        results = []
        interactions_sequence = scenario.interactions
        for interaction in interactions_sequence:
            payload = {"prompt": interaction.user_message}
            response = await async_request(
                url=self.endpoint,
                headers=self.headers,
                payload=payload,
            )
            if not response or not response.status_code == 200:
                add_event("ERROR", "Inbound interaction request failed.", {
                    "status_code": response.status_code if response else "No response",
                    "conversation_id": interaction.id,
                    "user_message": interaction.user_message
                })
                result = {
                    "user_message": interaction.user_message,
                    "agent_reply": "Request failed",
                    "reference_reply": getattr(interaction, 'reference_reply', None),
                    "interaction_type": getattr(interaction, 'interaction_type', None),
                    "reference_metadata": getattr(interaction, 'reference_metadata', {}),
                    "generated_metadata": {},
                    "evaluation_results": {},
                }
                results.append(result)
                continue
    
            # interaction_details = extract_interaction_details(response_text=response.text)
            evaluation_results= await self.evaluate_interaction(interaction.user_message, interaction.reference_reply)
            # evaluation_results = None
            # if self.evaluation_fn:
            #     evaluation_results = self.evaluation_fn(
            #         extracted_reply=response.text,
            #         reference_reply=getattr(interaction, 'reference_reply', None),
            #         generated_metadata= {},
            #         reference_metadata=getattr(interaction, 'reference_metadata', {}),
            #         scenario_id=getattr(scenario, 'scenario_id', 'unknown')
            #     )

            # actual_handoff = interaction_details.handoff_details is not None
            # expected_handoff = getattr(interaction, 'expected_handoff_pass', False)
            # handoff_pass_check = 1 if expected_handoff == actual_handoff else 0
            result = {
                "user_message": interaction.user_message,
                "agent_reply": response.text,
                "reference_reply": getattr(interaction, 'reference_reply', None),
                "interaction_type": None,
                "reference_metadata": getattr(interaction, 'reference_metadata', {}),
                "generated_metadata": {},
                "evaluation_results": evaluation_results,
            }
            results.append(result)
        print(f"Here is the results: ", results)
        return  results
    async def evaluate_interaction(
            self,
            extracted_vla_reply: str,
            reference_vla_reply: str,
            # extracted_metadata: Dict[str, Any],
            # reference_metadata: Dict[str, Any],
            # scenario_title: str
    ):
    # -> InteractionEvaluationResult:
        """
        Evaluate an interaction using OpenAI and Ionos evaluation services.

        Args:
            extracted_vla_reply (str): The extracted VLA reply.
            reference_vla_reply (str): The reference VLA reply.
            extracted_metadata (Dict[str, Any]): The extracted metadata.
            reference_metadata (Dict[str, Any]): The reference metadata.

        Returns:
            InteractionEvaluationResult: The evaluation results.
        """
        openai_eval_task = self.evaluation_service.evaluate_response(
            provider="openai",
            output_text=extracted_vla_reply,
            reference_text=reference_vla_reply,
        )

        ionos_eval_task = self.evaluation_service.evaluate_response(
            provider="ionos",
            output_text=extracted_vla_reply,
            reference_text=reference_vla_reply,
        )

        openai_reply_evaluation, ionos_reply_evaluation = await asyncio.gather(openai_eval_task, ionos_eval_task)

        # extracted_metadata_evaluation = evaluate_metadata(
        #     expected=reference_metadata,
        #     actual=extracted_metadata,
        #     field_types={}
        # )

        return {
            "openai": openai_reply_evaluation,
            "ionos": ionos_reply_evaluation,
        }

        # return InteractionEvaluationResult(
        #     openaiReplyEvaluation=openai_reply_evaluation,
        #     ionosReplyEvaluation=ionos_reply_evaluation,
        #     extractedMetadataEvaluation=extracted_metadata_evaluation,
        #     scenarioTitle=scenario_title
        # )

    # def store_evaluation_results(self, results: InteractionEvaluationResult) -> None:
    #     """
    #     Store the evaluation results in the evaluation summary.

    #     Args:
    #         results (InteractionEvaluationResult): The evaluation results to store.
    #     """
    #     self.evaluation_results["openaiJustificationSummary"].append({
    #         "scenario": results.scenarioTitle,
    #         "justification": results.openaiReplyEvaluation.justification
    #     })
    #     self.evaluation_results["ionosJustificationSummary"].append({
    #         "scenario": results.scenarioTitle,
    #         "justification": results.ionosReplyEvaluation.justification
    #     })
        
    #     self.collected_scores["openai"].append(results.openaiReplyEvaluation.match_level)
    #     self.collected_scores["ionos"].append(results.ionosReplyEvaluation.match_level)
    #     self.collected_scores["metadata"].append(results.extractedMetadataEvaluation)