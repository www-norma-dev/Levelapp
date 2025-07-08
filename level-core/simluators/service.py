"""
levelapp_core_simulators/service.py: Generic service layer for conversation simulation and evaluation.
"""
import asyncio
import logging
import time
from typing import Dict, Any, List, Callable, Optional
from collections import defaultdict
from datetime import datetime
from .schemas import InteractionEvaluationResult
from .utils import (
    extract_interaction_details,
    async_request,
    parse_date_value,
    calculate_average_scores,
    summarize_justifications,
    calculate_handoff_stats,
    calculate_average_time_duration,
)

class ConversationSimulator:
    """
    Generic service to simulate conversations and evaluate interactions.
    """
    def __init__(self, batch: Any, logger: logging.Logger, evaluation_fn: Optional[Callable] = None, persistence_fn: Optional[Callable] = None):
        """
        Initialize the ConversationSimulator.
        Args:
            batch (Any): The batch of scenarios to simulate (user supplies structure).
            logger (logging.Logger): Logger instance.
            evaluation_fn (Callable): Function to evaluate interactions (user supplies).
            persistence_fn (Callable): Function to persist results (user supplies).
        """
        self.logger = logger
        self.batch = batch
        self.evaluation_fn = evaluation_fn  # User-supplied evaluation logic
        self.persistence_fn = persistence_fn  # User-supplied persistence logic
        self.collected_scores = defaultdict(list)
        self.evaluation_summaries = defaultdict(list)

    def setup_simulator(self, endpoint: str, headers: Dict[str, str]):
        """
        Set up the simulator with endpoint and headers.
        """
        self.endpoint = endpoint
        self.headers = headers

    async def run_batch_test(self, name: str, test_load: Dict[str, Any], attempts: int = 1) -> Dict[str, Any]:
        """
        Run a batch test for the given batch name and details.
        """
        self.logger.info(f"[run_batch_test] Starting batch test for batch: {name}")
        started_at = datetime.now().isoformat()
        start_time = time.time()
        results = await self.simulate_conversation(attempts=attempts)
        finished_at = datetime.now().isoformat()
        elapsed_time = time.time() - start_time
        average_execution_time = calculate_average_time_duration(results["scenarios"])
        test_load["results"] = {
            "startedAt": started_at,
            "finishedAt": finished_at,
            "totalDurationSeconds": elapsed_time,
            "globalJustification": self.evaluation_summaries,
            "averageScores": results["averageScores"],
            "scenarios": results["scenarios"],
            "averageExecutionTime": average_execution_time,
        }
        if self.persistence_fn:
            self.persistence_fn(test_load)
        return {"status": "COMPLETE"}

    async def simulate_conversation(self, attempts: int = 1) -> Dict[str, Any]:
        """
        Simulate conversations for all scenarios in the batch.
        """
        self.logger.info("[simulate_conversation] starting conversation simulation..")
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
        overall_average_scores = calculate_average_scores(aggregate_scores)
        for provider, justifications in self.evaluation_summaries.items():
            self.evaluation_summaries[provider] = summarize_justifications(
                justifications=justifications
            )
        all_handoff_vals: List[float] = []
        for scen in results:
            for attempt in scen.get("attempts", []):
                val = attempt.get("handoffPassAverage")
                if isinstance(val, (int, float)):
                    all_handoff_vals.append(val)
        handoff_avg_map = calculate_average_scores({"handoff": all_handoff_vals})
        overall_average_scores["handoff"] = handoff_avg_map.get("handoff", 0.0)
        return {
            "scenarios": results,
            "averageScores": overall_average_scores,
        }

    async def simulate_single_scenario(self, scenario: Any, attempts: int = 1) -> Dict[str, Any]:
        """
        Simulate a single scenario with the given number of attempts.
        """
        self.logger.info(f"[simulate_single_scenario] starting simulation for scenario: {getattr(scenario, 'scenario_id', 'unknown')}")
        attempt_results = []
        all_attempts_scores = defaultdict(list)
        for attempt in range(attempts):
            self.logger.info(f"[simulate_single_scenario] Running attempt: {attempt+1}/{attempts}")
            start_time = time.time()
            self.collected_scores = defaultdict(list)
            attempt_handoff_checks: List[int] = []
            conversation_id = f"batch-{attempt+1}"
            initial_interaction_results = await self.simulate_initial_interaction(
                scenario=scenario,
                conversation_id=conversation_id
            )
            attempt_handoff_checks.append(initial_interaction_results.get("handoffPassCheck", 0))
            inbound_interactions_results = await self.simulate_inbound_interactions(
                scenario=scenario,
                conversation_id=conversation_id
            )
            for r in inbound_interactions_results:
                if "handoffPassCheck" in r:
                    attempt_handoff_checks.append(r["handoffPassCheck"])
            single_attempt_scores = calculate_average_scores(self.collected_scores)
            for key in all_attempts_scores:
                all_attempts_scores[key].append(single_attempt_scores.get(key, 0.0))
            elapsed_time = time.time() - start_time
            handoff_stats = calculate_handoff_stats(attempt_handoff_checks)
            attempt_handoff_average = handoff_stats["average"]
            all_attempts_scores["handoff"].append(attempt_handoff_average)
            attempt_results.append({
                "attemptId": attempt + 1,
                "conversationId": conversation_id,
                "totalDurationSeconds": elapsed_time,
                "initialInteraction": initial_interaction_results,
                "inboundInteractions": inbound_interactions_results,
                "averageScores": single_attempt_scores,
                "handoffPassAverage": attempt_handoff_average,
                "executionTime": f"{elapsed_time:.2f}",
            })
        average_scores = calculate_average_scores(all_attempts_scores)
        return {
            "scenarioId": getattr(scenario, 'scenario_id', 'unknown'),
            "attempts": attempt_results,
            "averageScores": average_scores,
        }

    async def simulate_initial_interaction(self, scenario: Any, conversation_id: str) -> Dict[str, Any]:
        """
        Simulate the initial interaction for a scenario.
        """
        self.logger.info("[simulate_initial_interaction] Starting initial interaction simulation..")
        start_time = time.time()
        initial_interaction = getattr(scenario, 'initial_interaction', None)
        if initial_interaction is None:
            return {}
        initial_interaction.conversation_id = conversation_id
        expected_metadata = getattr(scenario, 'expected_metadata', {})
        # User must supply serialization logic for their scenario objects
        payload = getattr(initial_interaction, 'to_dict', lambda: dict())()
        response = await async_request(
            url=self.endpoint,
            headers=self.headers,
            payload=payload,
        )
        if not response or not response.status_code == 200:
            self.logger.error("[simulate_initial_interaction] Request failed.")
            return {
                "userMessage": getattr(initial_interaction, 'message', None),
                "reply": "Request failed",
                "expectedReply": getattr(scenario, 'expected_initial_reply', None),
                "extractedMetadata": {},
                "expectedMetadata": expected_metadata,
                "handoffDetails": None,
                "interactionType": "",
                "evaluationResults": {},
                "handoffPassCheck": 0,
            }
        interaction_details = extract_interaction_details(response_text=response.text)
        evaluation_results = None
        if self.evaluation_fn:
            evaluation_results = self.evaluation_fn(
                extracted_reply=interaction_details.reply,
                reference_reply=getattr(scenario, 'expected_initial_reply', None),
                extracted_metadata=interaction_details.extracted_metadata,
                reference_metadata=expected_metadata,
                scenario_id=getattr(scenario, 'scenario_id', 'unknown')
            )
        actual_handoff = interaction_details.handoff_details is not None
        expected_handoff = getattr(initial_interaction, 'expected_handoff_pass', False)
        handoff_pass_check = 1 if expected_handoff == actual_handoff else 0
        elapsed_time = time.time() - start_time
        return {
            "userMessage": getattr(initial_interaction, 'message', None),
            "reply": interaction_details.reply,
            "expectedReply": getattr(scenario, 'expected_initial_reply', None),
            "extractedMetadata": interaction_details.extracted_metadata,
            "expectedMetadata": expected_metadata,
            "handoffDetails": interaction_details.handoff_details,
            "interactionType": interaction_details.interaction_type,
            "evaluationResults": evaluation_results,
            "handoffPassCheck": handoff_pass_check,
            "executionTime": f"{elapsed_time:.2f}",
        }

    async def simulate_inbound_interactions(self, scenario: Any, conversation_id: str) -> List[Dict[str, Any]]:
        """
        Simulate inbound interactions for a scenario.
        """
        self.logger.info("[simulate_inbound_interactions] Starting inbound interactions simulation..")
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
                self.logger.error("[simulate_inbound_interaction] Request failed.")
                result = {
                    "userMessage": user_message,
                    "reply": "Request failed",
                    "expectedReply": getattr(interaction, 'expected_reply', None),
                    "extractedMetadata": {},
                    "expectedMetadata": {},
                    "evaluationResults": {},
                    "handoff": None,
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
            actual_handoff = interaction_details.handoff_details is not None
            expected_handoff = getattr(interaction, 'expected_handoff_pass', False)
            handoff_pass_check = 1 if expected_handoff == actual_handoff else 0
            result = {
                "userMessage": user_message,
                "reply": interaction_details.reply,
                "expectedReply": getattr(interaction, 'expected_reply', None),
                "extractedMetadata": interaction_details.extracted_metadata,
                "expectedMetadata": getattr(interaction, 'expected_metadata', {}),
                "evaluationResults": evaluation_results,
                "handoff": interaction_details.handoff_details,
                "handoffPassCheck": handoff_pass_check,
            }
            results.append(result)
        return results 