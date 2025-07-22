import asyncio
import json
from level_core.simluators.utils import async_request

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

if __name__ == "__main__":
    asyncio.run(init_rag("http://ionos.com"))
    asyncio.run(simple_chat_request())

