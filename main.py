import asyncio
import json
from level_core.simluators.utils import async_request
from level_core.simluators.schemas import BasicConversation, ConversationBatch
from level_core.simluators.service import ConversationSimulator
from level_core.evaluators.service import EvaluationService
from logging import Logger
from level_core.evaluators.schemas import EvaluationConfig
from dotenv import load_dotenv


async def init_rag(page_url: str):
    """
    Sends a request to the /init endpoint with the given page_url.
    """
    endpoint = "http://localhost:8000/init"
    headers = {
        "Content-Type": "application/json",
        "x-model-id": "meta-llama/Llama-3.3-70B-Instruct" 
    }
    payload = {
        "page_url": page_url,
    }
    print(f"Sending request to {endpoint} with payload: {json.dumps(payload)}")
    response = await async_request(endpoint, headers, payload)
    if response:
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        try:
            json_data = response.json()
            print(f"Parsed JSON: {json.dumps(json_data, indent=2)}")
        except json.JSONDecodeError:
            print("Response is not valid JSON")
    else:
        print("Request failed or returned None")

async def simple_chat_request():
    """
    Minimal example of using async_request to call any endpoint.
    """
    url = "http://localhost:8000/" 
    headers = {
        "Content-Type": "application/json",
        "x-model-id": "meta-llama/Llama-3.3-70B-Instruct"
    }
    payload = {
        "prompt": "Hello, what can you do?"
    }

    print(f"Sending request to {url} with payload: {json.dumps(payload)}")
    response = await async_request(url, headers, payload)

    if response:
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        try:
            json_data = response.json()
            print(f"Parsed JSON: {json.dumps(json_data, indent=2)}")
        except json.JSONDecodeError:
            print("Response is not valid JSON")
    else:
        print("Request failed or returned None")

def read_json_file(file_path: str):
    import json
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            return data
    except FileNotFoundError:
        print(f"[read_json_file] Error: File not found at {file_path}")
    except json.JSONDecodeError:
        print(f"[read_json_file] Error: Invalid JSON format in {file_path}")

if __name__ == "__main__":
    import os

    load_dotenv()  # Load environment variables from .env file
    try:
        evaluation_service = EvaluationService(logger=Logger("EvaluationService"))
        ionos_config = EvaluationConfig(
        api_url=os.getenv("IONOS_ENDPOINT"),
        api_key=os.getenv("IONOS_API_KEY"),
        model_id="0b6c4a15-bb8d-4092-82b0-f357b77c59fd",
        )
        openai_config = EvaluationConfig(
        api_url="",
        api_key=os.getenv("OPENAI_API_KEY"),
        model_id="",
        )

        evaluation_service.set_config(provider="ionos", config=ionos_config)
        evaluation_service.set_config(provider="openai", config=openai_config)
        endpoint = "http://localhost:8000"
        headers = {
            "Content-Type": "application/json",
            "x-model-id": "meta-llama/Llama-3.3-70B-Instruct" 
        }
        data= read_json_file("batch_test.json")
        batch_test= BasicConversation.model_validate(data["test_batch"])
        conversations_batch = ConversationBatch(
            conversations=[batch_test]
        )
        simulator= ConversationSimulator(conversations_batch, evaluation_service)
        simulator.setup_simulator(
            endpoint=endpoint,
            headers=headers
        )
        results= asyncio.run(simulator.run_batch_test(
            name="test_batch",
            test_load={},
            attempts=1
        ))
        print("Simulation results:", results)
    except Exception as e:
        print(f"Error loading batch test data: {e}")
