"""
Level Upgrade: Advanced Chatbot Evaluation Framework
====================================================

A comprehensive framework for chatbot evaluation using LLM-as-judge methodology
with support for local and cloud-based language models.

Key Components:
- ChatSimulator: Handles conversation simulation
- LocalEvaluator: Local LLM evaluation  
- ResultsExporter: JSON export functionality
- ScenarioRunner: Main orchestration class
"""

from .scenario_runner import ScenarioRunner
from .chat_simulator import ChatSimulator
from .exporters.results_exporter import ResultsExporter
from .evaluators.local_evaluator import LocalEvaluator
from .config import Config

__version__ = "1.0.0"
__author__ = "Level Core Team"

__all__ = [
    "ScenarioRunner",
    "ChatSimulator", 
    "ResultsExporter",
    "LocalEvaluator",
    "Config"
] 