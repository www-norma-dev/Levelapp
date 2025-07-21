"""
ChatSimulator class for handling conversation simulation with language models.
Supports both local and remote API endpoints.
"""

import json
import logging
from typing import List, Dict, Any, Optional
from level_core.simluators.utils import async_request
from .config import Config

logger = logging.getLogger(__name__)

class ChatSimulator:
    """Handles conversation simulation with language models."""
    
    def __init__(self, config: Config):
        """
        Initialize ChatSimulator with configuration.
        
        Args:
            config: Configuration object with API settings
        """
        self.config = config
        self.logger = logger
    
    async def init_rag(self, url: str) -> Dict[str, Any]:
        """
        Initialize RAG (Retrieval-Augmented Generation) with a source URL.
        
        Args:
            url: URL to initialize RAG with
            
        Returns:
            Initialization result
        """
        try:
            response = await async_request(
                url=f"{self.config.api_base_url}/init",
                headers={"Content-Type": "application/json"},
                payload={
                    "page_url": url,
                }
            )
            
            if response and response.status_code == 200:
                try:
                    return response.json()
                except json.JSONDecodeError:
                    return {"status": "success", "message": response.text}
            else:
                return {
                    "status": "error", 
                    "message": f"Failed to initialize RAG. Status: {response.status_code if response else 'No response'}"
                }
                
        except Exception as e:
            self.logger.error(f"Error initializing RAG: {e}")
            return {"status": "error", "message": f"Exception during RAG initialization: {str(e)}"}
    
    async def simulate_single_prompt(self, prompt: str, model_id: Optional[str] = None) -> str:
        """
        Simulate a single conversation turn.
        
        Args:
            prompt: User prompt to send to the model
            model_id: Optional model ID override
            
        Returns:
            Model response
        """
        # Use provided model_id or fall back to config
        active_model_id = model_id or self.config.model_id
        
        try:
            response = await async_request(
                url=self.config.api_base_url,
                headers={
                    "Content-Type": "application/json",
                    "x-model-id": active_model_id
                },
                payload={
                    "prompt": prompt,
                }
            )
            
            if response and response.status_code == 200:
                return self._parse_response(response)
            else:
                error_msg = f"Request failed with status: {response.status_code if response else 'No response'}"
                self.logger.error(error_msg)
                return f"Error: {error_msg}"
                
        except Exception as e:
            error_msg = f"Error processing prompt: {str(e)}"
            self.logger.error(error_msg)
            return f"Error: {error_msg}"
    
    async def simulate_conversation(self, prompts: List[str], model_id: Optional[str] = None) -> List[str]:
        """
        Simulate a complete conversation with multiple prompts.
        
        Args:
            prompts: List of user prompts to process sequentially
            model_id: Optional model ID override
            
        Returns:
            List of model replies in the same order as input prompts
        """
        replies = []
        
        self.logger.info(f"Starting conversation simulation with {len(prompts)} prompts")
        
        for i, prompt in enumerate(prompts, 1):
            self.logger.debug(f"Processing prompt {i}/{len(prompts)}: {prompt[:50]}...")
            
            reply = await self.simulate_single_prompt(prompt, model_id)
            replies.append(reply)
            
            self.logger.debug(f"Received reply {i}: {reply[:50]}...")
        
        self.logger.info(f"Conversation simulation completed. Generated {len(replies)} replies.")
        return replies
    
    def _parse_response(self, response) -> str:
        """
        Parse API response and extract the reply text.
        
        Args:
            response: HTTP response object
            
        Returns:
            Parsed reply text
        """
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
                
            return reply.strip() if isinstance(reply, str) else str(reply)
            
        except json.JSONDecodeError:
            # If JSON parsing fails, use raw text
            reply = response.text.strip()
            return reply if reply else "No response generated"
    
    def print_conversation(self, prompts: List[str], replies: List[str]):
        """
        Print a formatted conversation.
        
        Args:
            prompts: List of user prompts
            replies: List of model replies
        """
        print("\n📝 Conversation Results:")
        print("=" * 60)
        
        for i, (prompt, reply) in enumerate(zip(prompts, replies), 1):
            print(f"\nTurn {i}:")
            print(f"  👤 User: {prompt}")
            print(f"  🤖 Bot:  {reply}")
        
        print("\n" + "=" * 60)
    
    async def run_example_conversation(self) -> tuple[List[str], List[str]]:
        """
        Run an example conversation for testing purposes.
        
        Returns:
            Tuple of (prompts, replies)
        """
        example_prompts = [
            "Hello, how are you?",
            "What's the weather like?", 
            "Tell me a joke",
            "What's 2+2?",
            "Goodbye!"
        ]
        
        print("🤖 Running Example Chat Simulation...")
        replies = await self.simulate_conversation(example_prompts)
        
        self.print_conversation(example_prompts, replies)
        
        return example_prompts, replies 