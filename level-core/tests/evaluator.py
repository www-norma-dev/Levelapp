import uuid
import difflib
from typing import List, Dict

class LocalEvaluator:
    """
    Evaluator that compares the generated and expected responses locally.
    This uses string similarity to provide a score from 1 to 5.
    """

    def __init__(self):
        pass

    def compute_similarity_score(self, generated: str, expected: str) -> int:
        """
        Compare the generated response to the expected response and return a score from 1 to 5.
        
        Args:
            generated (str): The generated text from the bot.
            expected (str): The expected response for the same user input.

        Returns:
            int: A score between 1 and 5 based on similarity.
        """
        # Normalize to lowercase and strip spaces for better comparison
        generated = generated.strip().lower()
        expected = expected.strip().lower()

        # Calculate similarity ratio using difflib's SequenceMatcher
        similarity_ratio = difflib.SequenceMatcher(None, generated, expected).ratio()

        # Map the similarity ratio to a score from 1 to 5
        if similarity_ratio == 1.0:
            return 1  # Excellent match
        elif similarity_ratio >= 0.8:
            return 2  # Good match
        elif similarity_ratio >= 0.6:
            return 3  # Moderate match
        elif similarity_ratio >= 0.4:
            return 4  # Fair match
        else:
            return 5  # Poor match

    def compare_responses(self, generated: str, expected: str) -> Dict:
        """
        Compare the generated response to the expected response and return a score and justification.

        Args:
            generated (str): The generated text from the bot.
            expected (str): The expected response for the same user input.

        Returns:
            Dict: A dictionary with the evaluation score and justification.
        """
        score = self.compute_similarity_score(generated, expected)
        if score == 1:
            justification = "Exact match"
        elif score == 2:
            justification = "Close match with minor differences"
        elif score == 3:
            justification = "Moderate match with noticeable differences"
        elif score == 4:
            justification = "Fair match with several differences"
        else:
            justification = "Poor match with significant differences"

        return {"match_level": score, "justification": justification}

    def build_payload(self, test_cases: List[Dict]) -> Dict:
        """
        Prepare the payload to be sent to the FastAPI endpoint.

        Args:
            test_cases (List[Dict]): List of test cases with scenario, user message, etc.

        Returns:
            Dict: Structured JSON payload for evaluation.
        """
        return {"test_cases": test_cases}

    def evaluate(self, test_cases: List[Dict]) -> Dict:
        """
        Run the evaluation on a list of test cases.

        Args:
            test_cases (List[Dict]): A list of test cases that include scenario, user message, 
                                      generated response, and expected response.

        Returns:
            Dict: JSON structure with evaluation results.
        """
        results = []

        for case in test_cases:
            # Compare the generated response and expected response
            evaluation_result = self.compare_responses(case['bot_response'], case['expected_response'])

            results.append({
                "scenario": case['scenario'],
                "user_message": case['user_message'],
                "bot_response": case['bot_response'],
                "expected_response": case['expected_response'],
                "score": evaluation_result['match_level'],
                "justification": evaluation_result['justification']
            })

        return {"evaluation_results": results}
