import json
import asyncio
import os
from typing import List, Dict, Any, Optional
from level_core.simluators.utils import async_request
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def init_rag(url: str):
    response = await async_request(
        url= "http://127.0.0.1:8000/init",
        headers={"Content-Type": "application/json"},
        payload={
            f"page_url": url,
        }
    )
    if response and response.status_code == 200:
        try:
            return response.json()
        except:
            return {"status": "success", "message": response.text}
    return {"status": "error", "message": "Failed to initialize RAG"}

async def chat_simulation(prompts: List[str], model_id: Optional[str] = None) -> List[str]:
    """
    Simulate a conversation by processing a list of user prompts sequentially.
    
    Args:
        prompts: List of user prompts to process
        model_id: Model ID to use (defaults to environment variable)
        
    Returns:
        List of chatbot replies in the same order as input prompts
    """
    # Get model ID from environment or parameter
    if not model_id:
        model_id = os.getenv("MODEL_ID", "meta-llama/Llama-3.3-70B-Instruct")
    
    # Get API base URL from environment
    api_base_url = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
    
    replies = []
    
    for prompt in prompts:
        try:
            response = await async_request(
                url=api_base_url,
                headers={
                    "Content-Type": "application/json",
                    "x-model-id": model_id
                },
                payload={
                    "prompt": prompt,
                }
            )
            
            if response and response.status_code == 200:
                try:
                    # Try to parse as JSON first
                    response_data = response.json()
                    
                    # Handle different possible response formats
                    if isinstance(response_data, str):
                        # Simple string response
                        reply = response_data
                    elif isinstance(response_data, dict):
                        # Dictionary response - try common keys
                        reply = (response_data.get("response") or 
                                response_data.get("text") or 
                                response_data.get("content") or 
                                response_data.get("message") or 
                                response_data.get("output") or
                                str(response_data))
                    else:
                        reply = str(response_data)
                        
                    replies.append(reply.strip() if isinstance(reply, str) else str(reply))
                    
                except json.JSONDecodeError:
                    # If JSON parsing fails, use raw text
                    reply = response.text.strip()
                    replies.append(reply if reply else "No response generated")
                    
            else:
                # Handle failed requests
                error_msg = f"Request failed with status: {response.status_code if response else 'No response'}"
                replies.append(f"Error: {error_msg}")
                
        except Exception as e:
            # Handle any unexpected errors
            replies.append(f"Error processing prompt: {str(e)}")
    
    return replies

# Example usage functions
async def example_basic_simulation():
    """Example of basic chat simulation without context."""
    prompts = [
        "Hello, how are you?",
        "What's the weather like?",
        "Tell me a joke",
        "What's 2+2?",
        "Goodbye!"
    ]
    
    print("🤖 Running Basic Chat Simulation...")
    replies = await chat_simulation(prompts)
    
    print("\n📝 Results:")
    for i, (prompt, reply) in enumerate(zip(prompts, replies), 1):
        print(f"\nTurn {i}:")
        print(f"  User: {prompt}")
        print(f"  Bot:  {reply}")

async def main():
    """Main function to demonstrate the chat simulation functions."""
    print("🚀 Level Core Chat Simulation Demo")
    print("=" * 50)
    
    # Show environment configuration
    print(f"📡 API Base URL: {os.getenv('API_BASE_URL', 'http://127.0.0.1:8000')}")
    print(f"🤖 Model ID: {os.getenv('MODEL_ID', 'meta-llama/Llama-3.3-70B-Instruct')}")
    
    try:
        print("\n🔧 Initializing RAG...")
        init_result = await init_rag("https://www.ionos.com")
        print(f"RAG Init Result: {init_result}")
        
        # Run basic simulation example
        await example_basic_simulation()
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        print("💡 Make sure your local API server is running on the configured port!")

if __name__ == "__main__":
    asyncio.run(main())