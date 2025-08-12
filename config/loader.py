import yaml
import os
from typing import Dict, Any

def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path (str): Path to the configuration file
        
    Returns:
        dict: Configuration dictionary
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    
    return config

def get_database_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """
    Get database-specific configuration.
    
    Args:
        config_path (str): Path to the configuration file
        
    Returns:
        dict: Database configuration
    """
    config = load_config(config_path)
    return config.get("database", {})