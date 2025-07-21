"""
Utility functions for Level Upgrade framework.
Contains helper functions for logging, validation, and common operations.
"""

import logging
import os
from typing import Dict, Any, List
from datetime import datetime


def setup_logging(log_level: str = "INFO", log_file: str = None) -> logging.Logger:
    """
    Set up logging configuration for Level Upgrade.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional log file path
        
    Returns:
        Configured logger
    """
    # Create logger
    logger = logging.getLogger("level_upgrade")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def validate_prompts(prompts: List[str]) -> bool:
    """
    Validate a list of prompts.
    
    Args:
        prompts: List of prompts to validate
        
    Returns:
        True if valid, raises ValueError if not
    """
    if not prompts:
        raise ValueError("Prompts list cannot be empty")
    
    if not isinstance(prompts, list):
        raise ValueError("Prompts must be a list")
    
    for i, prompt in enumerate(prompts):
        if not isinstance(prompt, str):
            raise ValueError(f"Prompt {i+1} must be a string")
        
        if not prompt.strip():
            raise ValueError(f"Prompt {i+1} cannot be empty or whitespace only")
    
    return True


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def calculate_evaluation_metrics(scores: List[int]) -> Dict[str, Any]:
    """
    Calculate evaluation metrics from a list of scores.
    
    Args:
        scores: List of evaluation scores (0-3)
        
    Returns:
        Dictionary with calculated metrics
    """
    if not scores:
        return {
            "count": 0,
            "average": 0,
            "median": 0,
            "min": 0,
            "max": 0,
            "distribution": {0: 0, 1: 0, 2: 0, 3: 0}
        }
    
    # Basic statistics
    count = len(scores)
    average = sum(scores) / count
    median = sorted(scores)[count // 2]
    min_score = min(scores)
    max_score = max(scores)
    
    # Score distribution
    distribution = {i: scores.count(i) for i in range(4)}
    
    return {
        "count": count,
        "average": round(average, 2),
        "median": median,
        "min": min_score,
        "max": max_score,
        "distribution": distribution,
        "percentage_above_2": round((distribution[2] + distribution[3]) / count * 100, 1),
        "percentage_excellent": round(distribution[3] / count * 100, 1)
    }


def print_banner(title: str, width: int = 60):
    """
    Print a formatted banner.
    
    Args:
        title: Title to display
        width: Width of the banner
    """
    print("=" * width)
    print(f"{title:^{width}}")
    print("=" * width)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove extra spaces and trim
    filename = '_'.join(filename.split())
    
    # Ensure it's not too long
    if len(filename) > 200:
        filename = filename[:200]
    
    return filename


def get_timestamp_string() -> str:
    """
    Get current timestamp as formatted string.
    
    Returns:
        Timestamp string in YYYYMMDD_HHMMSS format
    """
    return datetime.now().strftime('%Y%m%d_%H%M%S')


def merge_configs(base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge two configuration dictionaries.
    
    Args:
        base_config: Base configuration
        override_config: Configuration to override with
        
    Returns:
        Merged configuration
    """
    merged = base_config.copy()
    merged.update(override_config)
    return merged


class ProgressTracker:
    """Simple progress tracker for long-running operations."""
    
    def __init__(self, total: int, description: str = "Processing"):
        self.total = total
        self.current = 0
        self.description = description
        self.start_time = datetime.now()
    
    def update(self, increment: int = 1):
        """Update progress by increment."""
        self.current += increment
        self._print_progress()
    
    def _print_progress(self):
        """Print current progress."""
        percentage = (self.current / self.total) * 100
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        print(f"\r{self.description}: {self.current}/{self.total} ({percentage:.1f}%) - "
              f"Elapsed: {format_duration(elapsed)}", end="", flush=True)
        
        if self.current >= self.total:
            print()  # New line when complete 