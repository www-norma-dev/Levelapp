"""
'evaluators/utils.py': Utility functions for value parsing, normalization, and similarity evaluation.
"""
import re
import datetime
from typing import Any, Optional, Dict

import Levenshtein


FIELD_PARSERS = {
    "beds": "float",
    "baths": "float",
    "budget": "float",
    "pets": "float",
    "moveInDate": "date",
}


def levenshtein_f1(a: str, b: str) -> float:
    """
    Computes an F1-like score using Levenshtein distance to approximate text similarity.

    Args:
        a (str): First string.
        b (str): Second string.

    Returns:
        float: F1 score between 0.0 and 1.0.
    """
    a, b = a.lower(), b.lower()
    if not a or not b:
        return 0.0

    distance = Levenshtein.distance(a, b)
    precision = (len(b) - distance) / len(b)
    recall = (len(a) - distance) / len(a)

    return 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0


def parse_float(val: Any) -> Optional[float]:
    """
    Attempt to parse a float from an arbitrary input.

    Args:
        val (Any): The value to parse.

    Returns:
        Optional[float]: Parsed float or None.
    """
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def parse_date(s: str) -> Optional[datetime.date]:
    """
    Attempt to parse a date from string using flexible formats.

    Args:
        s (str): Input date string.

    Returns:
        Optional[datetime.date]: Parsed date or None.
    """
    s = re.sub(r'[/.]', '-', s)
    for fmt in ('%d-%m-%Y', '%Y-%m-%d', '%m-%d-%Y'):
        try:
            return datetime.datetime.strptime(s, fmt).date()
        except ValueError:
            pass

    return None


def parse_value(field: str, raw_val: Any) -> Any:
    """
    Normalize a raw metadata field value based on expected type.

    Args:
        field (str): Field name (e.g., "beds", "moveInDate").
        raw_val (Any): Raw value to normalize.

    Returns:
        Any: Parsed or normalized value (float, date, or lowercase string).
    """
    parser_type = FIELD_PARSERS.get(field, "string")

    if parser_type == "float":
        return parse_float(raw_val)
    elif parser_type == "date":
        return parse_date(str(raw_val))

    return str(raw_val).strip().lower()


def compare_values(field: str, expected_val: Any, actual_val: Any) -> float:
    """
    Compare two values for a specific metadata field.

    Args:
        field (str): The field name (e.g., "budget").
        expected_val (Any): Ground truth value.
        actual_val (Any): Predicted or extracted value.

    Returns:
        float: Similarity score between 0.0 and 1.0.
    """
    parsed_exp = parse_value(field, expected_val)
    parsed_act = parse_value(field, actual_val)

    parser_type = FIELD_PARSERS.get(field)

    if parser_type == "float" and parsed_exp is not None and parsed_act is not None:
        return 1.0 if abs(parsed_exp - parsed_act) < 1e-6 else levenshtein_f1(str(expected_val), str(actual_val))

    if parser_type == "date" and parsed_exp and parsed_act:
        return 1.0 if parsed_exp == parsed_act else levenshtein_f1(str(expected_val), str(actual_val))

    return 1.0 if parsed_exp == parsed_act else levenshtein_f1(str(expected_val), str(actual_val))


def evaluate_metadata(expected: Dict[str, Any], actual: Dict[str, Any]) -> float:
    """
    Evaluate similarity between expected and actual metadata dictionaries.

    Args:
        expected (Dict[str, Any]): Reference metadata.
        actual (Dict[str, Any]): Extracted metadata.

    Returns:
        float: Average similarity score across all relevant fields.
    """
    fields = ["beds", "baths", "pets", "budget", "moveInDate"]
    relevant = [f for f in fields if f in expected]

    if not relevant:
        return 0.0

    scores = [compare_values(f, expected[f], actual.get(f)) for f in relevant]
    return sum(scores) / len(scores)