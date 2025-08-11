"""
'evaluators/utils.py': Utility functions for value parsing, normalization, and similarity evaluation.
"""

import re
import datetime
from typing import Any, Optional, Dict, Callable

from rapidfuzz import fuzz  # Using Rapidfuzz's fuzz module for text similarity

# Define a flexible parser registry for field types, which can be customized later.
FIELD_PARSERS: Dict[str, Callable[[Any], Any]] = {
    "float": lambda val: parse_float(val),
    "date": lambda val: parse_date(val),
    "string": lambda val: str(val).strip().lower(),
    # You can add more parsers for other types dynamically if needed
}

def levenshtein_f1(a: str, b: str) -> float:
    """
    Computes an F1-like score using Rapidfuzz's Levenshtein scorer to approximate text similarity.

    Args:
        a (str): First string.
        b (str): Second string.

    Returns:
        float: Similarity score between 0.0 and 1.0.
    """
    a, b = a.lower(), b.lower()
    if not a or not b:
        return 0.0

    # Using Rapidfuzz's Levenshtein score
    score = fuzz.ratio(a, b) / 100  # `fuzz.ratio()` gives a score from 0-100, so divide by 100 for 0-1 range
    return score


def parse_float(val: Any) -> Optional[float]:
    """
    Attempt to parse a float from an arbitrary input.

    Args:
        val (Any): The value to parse.

    Returns:
        Optional[float]: Parsed float or None if parsing fails.
    """
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def parse_date(s: str) -> Optional[datetime.date]:
    """
    Attempt to parse a date from a string using flexible formats.

    Args:
        s (str): Input date string.

    Returns:
        Optional[datetime.date]: Parsed date or None if parsing fails.
    """
    s = re.sub(r'[/.]', '-', s)
    for fmt in ('%d-%m-%Y', '%Y-%m-%d', '%m-%d-%Y'):
        try:
            return datetime.datetime.strptime(s, fmt).date()
        except ValueError:
            pass

    return None


def parse_value(field_type: str, raw_val: Any) -> Any:
    """
    Normalize a raw value based on the expected field type.

    Args:
        field_type (str): Expected field type (e.g., "float", "date", "string").
        raw_val (Any): Raw value to normalize.

    Returns:
        Any: Parsed or normalized value (float, date, or string).
    """
    parser = FIELD_PARSERS.get(field_type, FIELD_PARSERS["string"])  # Default to string if no parser is found
    return parser(raw_val)


def compare_values(field_type: str, expected_val: Any, actual_val: Any) -> float:
    """
    Compare two values for a specific field, using the appropriate parsing and similarity metrics.

    Args:
        field_type (str): The field's expected type (e.g., "float", "date").
        expected_val (Any): Ground truth value.
        actual_val (Any): Predicted or extracted value.

    Returns:
        float: Similarity score between 0.0 and 1.0.
    """
    parsed_exp = parse_value(field_type, expected_val)
    parsed_act = parse_value(field_type, actual_val)

    if field_type == "float" and parsed_exp is not None and parsed_act is not None:
        # Using exact match if the float values are within a very small tolerance.
        return 1.0 if abs(parsed_exp - parsed_act) < 1e-6 else levenshtein_f1(str(expected_val), str(actual_val))

    if field_type == "date" and parsed_exp and parsed_act:
        return 1.0 if parsed_exp == parsed_act else levenshtein_f1(str(expected_val), str(actual_val))

    # Default comparison (strings and fallback)
    return 1.0 if parsed_exp == parsed_act else levenshtein_f1(str(expected_val), str(actual_val))


def evaluate_metadata(expected: Dict[str, Any], actual: Dict[str, Any], field_types: Dict[str, str]) -> float:
    """
    Evaluate the similarity between expected and actual metadata dictionaries across dynamic fields.

    Args:
        expected (Dict[str, Any]): Reference metadata.
        actual (Dict[str, Any]): Extracted metadata.
        field_types (Dict[str, str]): Dictionary specifying the expected field type for each key.

    Returns:
        float: Average similarity score across all relevant fields.
    """
    relevant = [f for f in field_types if f in expected]

    if not relevant:
        return 0.0

    # Comparing values based on dynamic field types
    scores = [compare_values(field_types.get(f, "string"), expected[f], actual.get(f)) for f in relevant]
    return sum(scores) / len(scores)


# ---------------- Key Point Extraction (Heuristic) ---------------- #
def extract_key_point(text: str, max_words: int = 20) -> str:
    """Generate a concise one-line key point heuristic summary.

    Heuristics (fast, no external heavy NLP libs):
    1. Normalize whitespace and strip.
    2. If short enough already, return truncated to max_words.
    3. Split into sentences (., !, ?). Take the first non-trivial sentence.
    4. Tokenize words, remove very common stopwords, keep order of appearance of informative tokens.
    5. Reconstruct up to max_words; fall back to original snippet if filtering over-prunes.
    """
    if not text:
        return ""
    original = " ".join(text.strip().split())
    if not original:
        return ""

    # Early exit for very short strings
    words = original.split()
    if len(words) <= max_words:
        return original

    # Sentence segmentation (simple)
    import re as _re
    sentences = [s.strip() for s in _re.split(r'[.!?]\s+', original) if s.strip()]
    candidate = sentences[0] if sentences else original

    # Basic stopword list
    stop = {
        'the','a','an','of','to','and','or','in','on','for','with','is','are','was','were','be','this','that','it','as','by','at','from','your','you','i'
    }
    tokens = [t for t in _re.split(r'[^A-Za-z0-9_-]+', candidate) if t]
    filtered = []
    seen = set()
    for t in tokens:
        lt = t.lower()
        if lt in stop or len(lt) < 2:
            continue
        if lt in seen:
            continue
        seen.add(lt)
        filtered.append(t)

    # If filtering removed too much, fall back to original first sentence
    base_tokens = filtered if len(filtered) >= 4 else tokens
    summary = " ".join(base_tokens[:max_words])
    return summary
