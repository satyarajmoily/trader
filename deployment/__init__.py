"""
Deployment Package for Bitcoin Predictor System

This package provides deployment automation, infrastructure as code,
and environment management for production deployment.

Phase 5: Production Deployment & Enhanced Self-Correction
"""

from .docker_manager import DockerManager
from .environment_manager import EnvironmentManager

__all__ = [
    'DockerManager',
    'EnvironmentManager'
]

__version__ = '1.0.0' 