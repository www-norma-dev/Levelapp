"""
levelapp_core_simulators/event_collector.py: Shared event collection logic for simulators.
"""
from datetime import datetime
from typing import Optional, Dict, Any

# Global event list for demonstration; in production, this could be context-specific
execution_events = []

def add_event(level: str, message: str, context: Optional[Dict[str, Any]] = None):
    """
    Collects an execution event for the simulator.

    Args:
        level (str): The log level (e.g., 'INFO', 'ERROR').
        message (str): The event message.
        context (Optional[Dict[str, Any]], optional): Additional context for the event. Defaults to None.
    """
    execution_events.append({
        "timestamp": datetime.now().isoformat(),
        "level": level,
        "message": message,
        "context": context or {}
    }) 
    

def log_rag_event(level: str, message: str, extra_data: Dict[str, Any] = None):
    """
    Log RAG-specific events for tracking human-in-the-loop workflow.
    
    Args:
        level: Log level (INFO, ERROR, WARNING)
        message: Log message
        extra_data: Additional data to log
    """
    from datetime import datetime
    
    event_data = {
        "component": "rag_evaluation",
        "level": level,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    
    if extra_data:
        event_data.update(extra_data)
    
    add_event(level, f"[RAG] {message}", extra_data)