"""
levelapp_core_simulators/service.py: Generic service layer for conversation simulation and evaluation.
"""
import asyncio
import time
from typing import Dict, Any, List, Callable, Optional
from collections import defaultdict
from datetime import datetime
from .schemas import InteractionEvaluationResult
from .utils import (
    extract_interaction_details,
    async_request,
    parse_date_value,
    calculate_average,
    summarize_justifications,
    calculate_handoff_stats,
)
from .event_collector import add_event
from level_core.datastore.firestore.schemas import ScenarioBatch

class ConversationSimulator:
    """
    Generic service to simulate conversations and evaluate interactions.
    """
    def __init__(self, batch: ScenarioBatch, evaluation_fn: Optional[Callable] = None, persistence_fn: Optional[Callable] = None):
        """
        Initialize the ConversationSimulator.

        Args:
            batch (ScenarioBatch): The batch of scenarios to simulate (user supplies structure).
            evaluation_fn (Callable): Function to evaluate interactions (user supplies).
            persistence_fn (Callable): Function to persist results (user supplies).
        """
        self.batch = batch
        self.evaluation_fn = evaluation_fn  # User-supplied evaluation logic
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
        started_at = datetime.now().isoformat()
        start_time = time.time()
        results = await self.simulate_conversation(attempts=attempts)
        finished_at = datetime.now().isoformat()
        elapsed_time = time.time() - start_time
        average_execution_time = calculate_average(results["scenarios"])
        test_load["results"] = {
            "started_at": started_at,
            "finished_at": finished_at,
            "total_duration_seconds": elapsed_time,
            "global_justification": self.evaluation_summaries,
            "average_scores": results["average_scores"],
            "scenarios": results["scenarios"],
            "average_execution_time": average_execution_time,
            "execution_events": self.execution_events,  # (Legacy) - consider using event_collector.execution_events
        }
        if self.persistence_fn:
            self.persistence_fn(test_load)
        return {"status": "COMPLETE"}

    async def simulate_conversation(self, attempts: int = 1) -> Dict[str, Any]:
        """
        Simulate conversations for all scenarios in the batch.

        Args:
            attempts (int, optional): Number of attempts per scenario. Defaults to 1.

        Returns:
            Dict[str, Any]: The simulation results with scenarios and average scores.
        """
        add_event("INFO", "Starting conversation simulation..")
        semaphore = asyncio.Semaphore(value=len(self.batch.scenarios))
        async def run_with_semaphore(scenario: Any) -> Dict[str, Any]:
            async with semaphore:
                return await self.simulate_single_scenario(scenario=scenario, attempts=attempts)
        results = await asyncio.gather(*(run_with_semaphore(s) for s in self.batch.scenarios))
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

    async def simulate_single_scenario(self, scenario: Any, attempts: int = 1) -> Dict[str, Any]:
        """
        Simulate a single scenario with the given number of attempts.

        Args:
            scenario (Any): The scenario to simulate.
            attempts (int, optional): Number of attempts to run. Defaults to 1.

        Returns:
            Dict[str, Any]: The simulation results for the single scenario.
        """
        scenario_id = getattr(scenario, 'scenario_id', 'unknown')
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
            inbound_interactions_results = await self.simulate__interactions(
                scenario=scenario,
                conversation_id=conversation_id
            )
            for r in inbound_interactions_results:
                # if "handoffPassCheck" in r:
                #     attempt_handoff_checks.append(r["handoffPassCheck"])
                pass # Commented out handoff logic
            single_attempt_scores = calculate_average(self.collected_scores)
            for key in all_attempts_scores:
                all_attempts_scores[key].append(single_attempt_scores.get(key, 0.0))
            # elapsed_time = time.time() - start_time
            # handoff_stats = calculate_handoff_stats(attempt_handoff_checks)
            # attempt_handoff_average = handoff_stats["average"]
            # all_attempts_scores["handoff"].append(attempt_handoff_average)
            attempt_results.append({
                "attempt_id": attempt + 1,
                "conversation_id": conversation_id,
                # "totalDuration_seconds": elapsed_time,
                "initial_interaction": {}, # Commented out handoff logic
                "inbound_interactions": inbound_interactions_results,
                "average_scores": single_attempt_scores,
                "execution_time": f"{time.time() - start_time:.2f}", # Commented out handoff logic
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

    async def simulate__interactions(self, scenario: Any, conversation_id: str) -> List[Dict[str, Any]]:
        """
        Simulate inbound interactions for a scenario.

        Args:
            scenario (Any): The scenario to simulate.
            conversation_id (str): The conversation ID.

        Returns:
            List[Dict[str, Any]]: The results of the inbound interactions simulation.
        """
        add_event("INFO", "Starting inbound interactions simulation..")
        results = []
        inbound_interactions_sequence = getattr(scenario, 'inbound_interactions', [])
        for interaction in inbound_interactions_sequence:
            interaction.conversation_id = conversation_id
            user_message = getattr(interaction, 'message_content', None)
            payload = getattr(interaction, 'to_dict', lambda: dict())()
            response = await async_request(
                url=self.endpoint,
                headers=self.headers,
                payload=payload,
            )
            if not response or not response.status_code == 200:
                add_event("ERROR", "Inbound interaction request failed.", {
                    "status_code": response.status_code if response else "No response",
                    "conversation_id": conversation_id,
                    "user_message": user_message
                })
                result = {
                    "user_message": user_message,
                    "reply": "Request failed",
                    "expected_reply": getattr(interaction, 'expected_reply', None),
                    "extracted_metadata": {},
                    "expected_metadata": {},
                    "evaluation_results": {},
                }
                results.append(result)
                continue
            interaction_details = extract_interaction_details(response_text=response.text)
            evaluation_results = None
            if self.evaluation_fn:
                evaluation_results = self.evaluation_fn(
                    extracted_reply=interaction_details.reply,
                    reference_reply=getattr(interaction, 'expected_reply', None),
                    extracted_metadata=interaction_details.extracted_metadata,
                    reference_metadata=getattr(interaction, 'expected_metadata', {}),
                    scenario_id=getattr(scenario, 'scenario_id', 'unknown')
                )
            # actual_handoff = interaction_details.handoff_details is not None
            # expected_handoff = getattr(interaction, 'expected_handoff_pass', False)
            # handoff_pass_check = 1 if expected_handoff == actual_handoff else 0
            result = {
                "user_message": user_message,
                "reply": interaction_details.reply,
                "expected_reply": getattr(interaction, 'expected_reply', None),
                "extracted_metadata": interaction_details.extracted_metadata,
                "expected_metadata": getattr(interaction, 'expected_metadata', {}),
                "evaluation_results": evaluation_results,
            }
            results.append(result)
        return results