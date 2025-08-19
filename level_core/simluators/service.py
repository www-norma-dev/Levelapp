"""
levelapp_core_simulators/service.py: Generic service layer for conversation simulation and evaluation.
"""
import asyncio
import time
from typing import Dict, Any, List, Callable, Optional, cast
from collections import defaultdict
from datetime import datetime
from .schemas import InteractionEvaluationResult, Interaction, BasicConversation, ConversationBatch
from .utils import (
    extract_interaction_details,
    async_request,
    parse_date_value,
    calculate_average,
    summarize_justifications,
)
from .event_collector import add_event
from level_core.simluators.schemas import ConversationBatch
from level_core.evaluators.service import EvaluationService
from level_core.evaluators.utils import evaluate_metadata
from level_core.config.Adapter import EndpointConfig
from level_core.config.ResponseAdapter import adapt_agent_response
class ConversationSimulator:
    """
    Generic service to simulate conversations and evaluate interactions.
    """
    def __init__(self,
                 batch: ConversationBatch,
                 evaluation_service: EvaluationService,
                 persistence_fn: Optional[Callable] = None,
                 payload_adapter: Optional[Callable[[Any], Dict[str, Any]]] = None,
                 endpoint_configuration: Optional[EndpointConfig] = None):
        """Initialize the ConversationSimulator."""
        self.batch = batch
        self.evaluation_service = evaluation_service
        self.persistence_fn = persistence_fn
        self.collected_scores = defaultdict(list)
        self.evaluation_summaries = defaultdict(list)
        self.execution_events = []
        self.payload_adapter = payload_adapter
        self.endpoint_configuration = endpoint_configuration

    def setup_simulator(self, endpoint: Optional[str] = None, headers: Optional[Dict[str, str]] = None):
        """
        Set up the simulator with endpoint and headers, or use Adapter if available.
        """
        if self.endpoint_configuration:
            # Cast computed fields to satisfy type checker
            self.endpoint = cast(str, self.endpoint_configuration.full_url)
            self.headers = cast(Dict[str, str], self.endpoint_configuration.headers)
        else:
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
            conversation_id = f"batch-{attempt+1}"
            interactions_results = await self.simulate__interactions(
                scenario=scenario,
                conversation_id=conversation_id
            )

            single_attempt_scores = calculate_average(self.collected_scores)
            for key in all_attempts_scores:
                all_attempts_scores[key].append(single_attempt_scores)

            attempt_results.append({
                "attempt_id": attempt + 1,
                "conversation_id": conversation_id,
                "interactions": interactions_results, 
                "average_scores": single_attempt_scores,
                "execution_time": f"{time.time() - start_time:.2f}",
            })
        average_scores = calculate_average(all_attempts_scores)

        return {
            "scenario_id": scenario_id,
            "attempts": attempt_results,
            "average_scores": average_scores,
        }

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
            if self.endpoint_configuration:
                user_message = interaction.user_message
                # User should set the payload template in EndpointConfig, e.g. {"prompt": "${user_message}"}
                self.endpoint_configuration.variables = {"user_message": user_message}
                payload = cast(Dict[str, Any], self.endpoint_configuration.payload)
                response = await async_request(
                    url=cast(str, self.endpoint_configuration.full_url),
                    headers=cast(Dict[str, str], self.endpoint_configuration.headers),
                    payload=payload,
                )
            else:
                payload = {"prompt": interaction.user_message}
                response = await async_request(
                    url=cast(str, self.endpoint),
                    headers=cast(Dict[str, str], self.headers),
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
    
            # Previous behavior (kept for reference):
            # evaluation_results = await self.evaluate_interaction(response.text, interaction.reference_reply)
            # New behavior: adapt any response shape to a clean text string
            agent_text = adapt_agent_response(response)
            evaluation_results = await self.evaluate_interaction(agent_text, interaction.reference_reply)
    
            result = {
                "user_message": interaction.user_message,
                # "agent_reply": response.text,  # previous raw text
                "agent_reply": agent_text,
                "reference_reply": getattr(interaction, 'reference_reply', None),
                "interaction_type": None,
                "reference_metadata": getattr(interaction, 'reference_metadata', {}),
                "generated_metadata": {},
                "evaluation_results": evaluation_results,
            }
            results.append(result)
        return  results
    async def evaluate_interaction(
            self,
            extracted_reply: str,
            reference_reply: str,
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
            output_text=extracted_reply,
            reference_text=reference_reply,
        )

        ionos_eval_task = self.evaluation_service.evaluate_response(
            provider="ionos",
            output_text=extracted_reply,
            reference_text=reference_reply,
        )

        openai_reply_evaluation, ionos_reply_evaluation = await asyncio.gather(openai_eval_task, ionos_eval_task)

        return {
            "openai": openai_reply_evaluation,
            "ionos": ionos_reply_evaluation,
        }
