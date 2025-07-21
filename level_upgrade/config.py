"""
Configuration management for Level Upgrade framework.
Handles environment variables, API settings, and default configurations.
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class Config:
    """Configuration class for Level Upgrade framework."""
    
    # API Configuration
    api_base_url: str = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
    model_id: str = os.getenv("MODEL_ID", "meta-llama/Llama-3.3-70B-Instruct")
    
    # Evaluator Configuration
    evaluator_api_url: str = os.getenv("EVALUATOR_API_URL", None)
    evaluator_model_id: str = os.getenv("EVALUATOR_MODEL_ID", None)
    evaluator_api_key: str = os.getenv("EVALUATOR_API_KEY", "dummy-key")
    
    # OpenAI Configuration (if using OpenAI evaluator)
    openai_api_url: str = os.getenv("OPENAI_API_URL", "https://api.openai.com/v1/chat/completions")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", None)
    openai_model_id: str = os.getenv("OPENAI_MODEL_ID", "gpt-4o-mini")
    
    # Output Configuration
    results_output_dir: str = os.getenv("RESULTS_OUTPUT_DIR", "results")
    
    # LLM Configuration
    llm_config: Dict[str, Any] = None
    
    def __post_init__(self):
        """Post-initialization setup."""
        # Set default evaluator URLs if not specified
        if not self.evaluator_api_url:
            self.evaluator_api_url = self.api_base_url
        if not self.evaluator_model_id:
            self.evaluator_model_id = self.model_id
            
        # Set default LLM config
        if self.llm_config is None:
            self.llm_config = {
                "temperature": 0.1,
                "max_tokens": 200
            }
    
    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        return cls()
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "Config":
        """Create configuration from dictionary."""
        return cls(**config_dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "api_base_url": self.api_base_url,
            "model_id": self.model_id,
            "evaluator_api_url": self.evaluator_api_url,
            "evaluator_model_id": self.evaluator_model_id,
            "evaluator_api_key": self.evaluator_api_key,
            "openai_api_url": self.openai_api_url,
            "openai_api_key": self.openai_api_key,
            "openai_model_id": self.openai_model_id,
            "results_output_dir": self.results_output_dir,
            "llm_config": self.llm_config
        }
    
    def validate(self) -> bool:
        """Validate configuration."""
        required_fields = ["api_base_url", "model_id"]
        
        for field in required_fields:
            if not getattr(self, field):
                raise ValueError(f"Configuration field '{field}' is required")
        
        return True
    
    def print_config(self):
        """Print current configuration (hiding sensitive data)."""
        print("🔧 Level Upgrade Configuration:")
        print(f"   📡 API Base URL: {self.api_base_url}")
        print(f"   🤖 Model ID: {self.model_id}")
        print(f"   🔍 Evaluator URL: {self.evaluator_api_url}")
        print(f"   🧠 Evaluator Model: {self.evaluator_model_id}")
        print(f"   📁 Results Directory: {self.results_output_dir}")
        print(f"   ⚙️  LLM Config: {self.llm_config}")
        
        # Show API keys availability (but not actual values)
        api_key_status = "✅ Set" if self.evaluator_api_key and self.evaluator_api_key != "dummy-key" else "⚠️ Default/Missing"
        openai_key_status = "✅ Set" if self.openai_api_key else "❌ Missing"
        print(f"   🔑 Evaluator API Key: {api_key_status}")
        print(f"   🔑 OpenAI API Key: {openai_key_status}") 