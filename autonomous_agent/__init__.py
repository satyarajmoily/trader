"""
Autonomous Agent System for Bitcoin Prediction Improvement

This package contains the AI agent system that orchestrates Bitcoin prediction
evaluation and improvement. It works with the core bitcoin_predictor system
through clean interfaces.
"""

from .orchestrator import AutonomousAgent
from .interfaces.predictor_interface import PredictorInterface

__version__ = "1.0.0"
__all__ = [
    "AutonomousAgent",
    "PredictorInterface"
] 