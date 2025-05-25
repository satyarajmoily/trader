"""
Monitoring Package for Bitcoin Predictor System

This package provides comprehensive monitoring, health checking, and observability
capabilities for both the core prediction system and autonomous agent.

Phase 5: Production Deployment & Enhanced Self-Correction
"""

from .health_checker import HealthChecker
from .metrics_collector import MetricsCollector
from .alerting import AlertManager

__all__ = [
    'HealthChecker',
    'MetricsCollector', 
    'AlertManager'
]

__version__ = '1.0.0' 