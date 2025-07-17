def evaluate_result(user_input: str, response: str) -> dict:
    # Simple rule-based scoring logic
    score = 1.0 if "help" in response.lower() else 0.5
    return {
        "score": score,
        "comment": "Good response" if score > 0.7 else "Needs improvement"
    }
