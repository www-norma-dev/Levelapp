# evaluation_api.py
from fastapi import FastAPI
from pydantic import BaseModel
import requests
from typing import List
from difflib import SequenceMatcher

app = FastAPI()

class Scenario(BaseModel):
    scenario: str
    user_message: str
    expected_response: str

class EvaluationRequest(BaseModel):
    endpoint: str  # at http://localhost:8000 the chatbot simulator
    model_id: str
    attempt: str
    presetName: str
    presetDescription: str
    scenarios: List[Scenario]

@app.post("/evaluate")
def evaluate_chatbot(data: EvaluationRequest):
    results = []

    for scenario in data.scenarios:
        try:
            response = requests.post(
                f"{data.endpoint}/ask",
                json={"message": scenario.user_message}
            )
            response.raise_for_status()
            bot_response = response.json().get("response", "")
        except Exception as e:
            bot_response = f"Error during simulation: {e}"

        score = round(SequenceMatcher(None, bot_response, scenario.expected_response).ratio(), 2)
        results.append({
            "scenario": scenario.scenario,
            "user_message": scenario.user_message,
            "bot_response": bot_response,
            "expected_response": scenario.expected_response,
            "score": score
        })

    return {"evaluation_results": results}
