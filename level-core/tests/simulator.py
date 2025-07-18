import requests

def run_simulation(endpoint: str, message: str) -> str:
    try:
        response = requests.post(
            url=endpoint,
            json={"message": message},
            timeout=5
        )
        response.raise_for_status()
        data = response.json()
        return data.get("response", "")
    except Exception as e:
        return f"Error during simulation: {str(e)}"
