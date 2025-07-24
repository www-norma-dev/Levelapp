"""
levelapp_core_simulators/utils.py: Generic utility functions for simulation and evaluation.
"""
import json
from typing import Dict, Any, Optional, List, Union
import httpx
import arrow
from pydantic import ValidationError
from collections import defaultdict
from .schemas import InteractionDetails
from .event_collector import add_event
from rouge_score import rouge_scorer


def extract_interaction_details(response_text: str) -> InteractionDetails:
    """
    Extracts interaction details from a response text.

    Args:
        response_text (str): The response text in JSON format.

    Returns:
        InteractionDetails: Parsed interaction details, or default if parsing fails.
    """
    print("I'm now in extract_interaction_details", "data passed in:", response_text)
    try:
        data = json.loads(response_text)
        payload = data.get("payload", {})
        print("Here is the payload: ",payload)
        return InteractionDetails(
            reply=payload.get("message", "No response"),
            extracted_metadata=payload.get("metadata", {}),
        )
    except json.JSONDecodeError as err:
        msg = f"[extract_interaction_details] JSON decoding error: {err}"
        add_event("ERROR", msg)
        return InteractionDetails()
    except ValidationError as err:
        msg = f"[extract_interaction_details] Pydantic validation error: {err}"
        add_event("ERROR", msg)
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
        msg = f"[async_request] Request payload:\n{payload}\n---"
        add_event("INFO", msg)
        async with httpx.AsyncClient(timeout=900) as client:
            response = await client.post(url=url, headers=headers, json=payload)
            msg = f"[async_request] Response:\n{response.text}\n---"
            add_event("INFO", msg)
            response.raise_for_status()
            return response
    except httpx.HTTPStatusError as http_err:
        msg = f"[async_request] HTTP error: {http_err.response.text}"
        add_event("ERROR", msg, {"exc_info": True})
    except httpx.RequestError as req_err:
        msg = f"[async_request] Request error: {str(req_err)}"
        add_event("ERROR", msg, {"exc_info": True})
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
        msg = f"[parse_date_value] No raw value provided. returning default: '{default_date_value}'"
        add_event("INFO", msg)
        return default_date_value
    cleaned = raw_date_value.replace("{{", "").replace("}}", "").replace("_", " ").strip().lower()
    now = arrow.utcnow()
    try:
        iso_candidate = cleaned.replace(" ", "-")
        return arrow.get(iso_candidate).format("YYYY-MM-DD")
    except Exception:
        pass
    try:
        return now.dehumanize(cleaned).format("YYYY-MM-DD")
    except Exception as e:
        msg = f"[parse_date_value] Failed to parse '{cleaned}': {e}"
        add_event("ERROR", msg, {"exc_info": True})
        return default_date_value


def calculate_average(data: Union[Dict[str, List[float]], List[Dict[str, Any]]]) -> Union[Dict[str, float], float]:
    """
    Calculates averages depending on input type.

    Args:
        data (Union[Dict[str, List[float]], List[Dict[str, Any]]]): Either a dictionary of lists or a list of scenario dicts.

    Returns:
        Union[Dict[str, float], float]: Averaged result(s) - dict of averages per key or single average duration.
    """
    if isinstance(data, dict):  # case for score dictionary
        return {
            key: round(sum(values) / len(values), 3) if values else 0.0
            for key, values in data.items()
        }
    elif isinstance(data, list):  # case for scenarios
        durations = [
            attempt["totalDurationSeconds"]
            for scenario in data
            for attempt in scenario.get("attempts", [])
            if isinstance(attempt.get("totalDurationSeconds"), (int, float))
        ]
        return round(sum(durations) / len(durations), 2) if durations else 0.0
    else:
        raise TypeError("Unsupported data type for average calculation.")
    
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
    return merged_justifications[:max_bullets] 