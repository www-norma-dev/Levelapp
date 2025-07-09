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