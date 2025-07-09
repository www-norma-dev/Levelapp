"""
levelapp_core_simulators/utils.py: Generic utility functions for simulation and evaluation.
"""
import json
import logging
from typing import Dict, Any, Optional, List
import httpx
import arrow
from pydantic import ValidationError
from collections import defaultdict
from .schemas import InteractionDetails, RelativeDateOption

logger = logging.getLogger("simulator-utils")


def extract_interaction_details(response_text: str) -> InteractionDetails:
    """
    Extracts interaction details from a response text.

    Args:
        response_text (str): The response text in JSON format.

    Returns:
        InteractionDetails: Parsed interaction details, or default if parsing fails.
    """
    try:
        data = json.loads(response_text)
        payload = data.get("payload", {})
        return InteractionDetails(
            reply=payload.get("message", "No response"),
            extracted_metadata=payload.get("metadata", {}),
            handoff_details=payload.get("handoffMetadata", {}),
            interaction_type=payload.get("eventType", ""),
        )
    except json.JSONDecodeError as err:
        logger.error(f"[extract_interaction_details] JSON decoding error: {err}")
        return InteractionDetails()
    except ValidationError as err:
        logger.error(f"[extract_interaction_details] Pydantic validation error: {err}")
        return InteractionDetails()


async def async_request(url: str, headers: Dict[str, str], payload: Dict[str, Any]) -> Optional[httpx.Response]:
    """
    Performs an asynchronous HTTP POST request.

    Args:
        url (str): The endpoint URL.
        headers (Dict[str, str]): HTTP headers to include in the request.
        payload (Dict[str, Any]): The JSON payload to send.

    Returns:
        Optional[httpx.Response]: The HTTP response if successful, otherwise None.
    """
    try:
        logger.info(f"[async_request] Request payload:\n{payload}\n---")
        async with httpx.AsyncClient(timeout=900) as client:
            response = await client.post(url=url, headers=headers, json=payload)
            logger.info(f"[async_request] Response:\n{response.text}\n---")
            response.raise_for_status()
            return response
    except httpx.HTTPStatusError as http_err:
        logger.error(f"[async_request] HTTP error: {http_err.response.text}", exc_info=True)
    except httpx.RequestError as req_err:
        logger.error(f"[async_request] Request error: {str(req_err)}", exc_info=True)
    return None


def parse_date_value(raw_date_value: Optional[str], default_date_value: Optional[str] = "") -> str:
    """
    Cleans and parses a dehumanized relative date string to ISO format.

    Args:
        raw_date_value (Optional[str]): The raw date string to parse.
        default_date_value (Optional[str], optional): The default value to return if parsing fails. Defaults to "".

    Returns:
        str: The parsed date in ISO format, or the default value if parsing fails.
    """
    if not raw_date_value:
        logger.info(f"[parse_date_value] No raw value provided. returning default: '{default_date_value}'")
        return default_date_value
    cleaned = raw_date_value.replace("{{", "").replace("}}", "").replace("_", " ").strip().lower()
    now = arrow.utcnow()
    try:
        option = RelativeDateOption(cleaned)
        match option:
            case RelativeDateOption.TODAY:
                return now.format("YYYY-MM-DD")
            case RelativeDateOption.TOMORROW:
                return now.shift(days=1).format("YYYY-MM-DD")
            case RelativeDateOption.TODAY_PLUS_7:
                return now.shift(days=7).format("YYYY-MM-DD")
            case RelativeDateOption.IN_1_MONTH:
                return now.shift(months=1).floor("month").format("YYYY-MM-DD")
            case RelativeDateOption.IN_2_MONTHS:
                return now.shift(months=2).floor("month").format("YYYY-MM-DD")
            case RelativeDateOption.IN_3_MONTHS:
                return now.shift(months=3).floor("month").format("YYYY-MM-DD")
            case RelativeDateOption.IN_4_MONTHS:
                return now.shift(months=4).floor("month").format("YYYY-MM-DD")
    except ValueError:
        pass
    try:
        iso_candidate = cleaned.replace(" ", "-")
        return arrow.get(iso_candidate).format("YYYY-MM-DD")
    except Exception:
        pass
    try:
        return now.dehumanize(cleaned).format("YYYY-MM-DD")
    except Exception as e:
        logger.error(f"[parse_date_value] Failed to parse '{cleaned}': {e}", exc_info=True)
        return default_date_value


def calculate_average_scores(scores: Dict[str, List[float]]) -> Dict[str, float]:
    """
    Calculates the average scores for a dictionary of score lists.

    Args:
        scores (Dict[str, List[float]]): A dictionary mapping keys to lists of scores.

    Returns:
        Dict[str, float]: A dictionary mapping keys to their average score.
    """
    def average(values: List[float]) -> float:
        return round(sum(values) / len(values), 3) if values else 0.0
    return {key: average(values) for key, values in scores.items()}


def calculate_handoff_stats(values: List[Any]) -> Dict[str, Any]:
    """
    Computes statistics for handoff pass check values.

    Args:
        values (List[Any]): List of handoff pass check values (0, 1, or None).

    Returns:
        Dict[str, Any]: Dictionary with the raw values and the average over valid entries.
    """
    raw = list(values)
    clean = [v for v in raw if isinstance(v, int) and v in (0, 1)]
    avg = round(sum(clean) / len(clean), 3) if clean else 0.0
    return {"values": raw, "average": avg}


def calculate_average_time_duration(scenarios: List[Dict[str, Any]]) -> float:
    """
    Calculates the average execution time across all attempts in all scenarios.

    Args:
        scenarios (List[Dict[str, Any]]): List of scenario dictionaries, each containing attempts.

    Returns:
        float: The average execution time in seconds, or 0.0 if no durations are found.
    """
    durations = []
    for scenario in scenarios:
        for attempt in scenario.get("attempts", []):
            duration = attempt.get("totalDurationSeconds")
            if isinstance(duration, (int, float)):
                durations.append(duration)
    if not durations:
        return 0.0
    return round(sum(durations) / len(durations), 2)


def calculate_rouge_scores(reference: str, candidate: str, metrics: Optional[List[str]] = None, use_stemmer: bool = True) -> Dict[str, Dict[str, float]]:
    """
    Calculates ROUGE scores for a candidate reply against a single reference.

    Args:
        reference (str): The reference text.
        candidate (str): The candidate text to evaluate.
        metrics (Optional[List[str]], optional): List of ROUGE metrics to compute. Defaults to ['rouge1', 'rouge2', 'rougeL'].
        use_stemmer (bool, optional): Whether to use stemming. Defaults to True.

    Returns:
        Dict[str, Dict[str, float]]: Dictionary of ROUGE scores for each metric.
    """
    from rouge_score import rouge_scorer
    if metrics is None:
        metrics = ['rouge1', 'rouge2', 'rougeL']
    scorer = rouge_scorer.RougeScorer(metrics, use_stemmer=use_stemmer)
    scores = scorer.score(reference, candidate)
    result = {}
    for m in metrics:
        result[m] = {
            'precision': scores[m].precision,
            'recall': scores[m].recall,
            'fmeasure': scores[m].fmeasure
        }
    return result


def summarize_justifications(justifications: List[Dict[str, str]], max_bullets: int = 5) -> List[str]:
    """
    Summarizes the justifications for each judge.

    Args:
        justifications (List[Dict[str, str]]): List of justification dictionaries with 'justification' and 'scenario'.
        max_bullets (int, optional): Maximum number of summarized justifications to return. Defaults to 5.

    Returns:
        List[str]: List of summarized justifications, grouped by justification text.
    """
    # Placeholder: implement your own summarization logic or LLM call here
    grouped = defaultdict(list)
    for item in justifications:
        grouped[item["justification"].strip()].append(item["scenario"])
    merged_justifications = [
        f"{justification} (Scenarios: {', '.join(scenarios)})"
        for justification, scenarios in grouped.items()
    ]
    # Return up to max_bullets merged justifications
    return merged_justifications[:max_bullets] 