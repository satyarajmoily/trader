"""
Bitcoin Predictor Core System

A standalone Bitcoin price prediction system using OHLCV data analysis.
This package is independent of any agent systems and can be used standalone.
"""

from .predictor import BitcoinPredictor
from .models import PredictionResult, OHLCVData, PredictionRecord
from .interfaces import PredictionInterface
from .data_loader import BitcoinDataLoader
from .storage import PredictionStorage

__version__ = "1.0.0"
__all__ = [
    "BitcoinPredictor",
    "PredictionResult", 
    "OHLCVData",
    "PredictionRecord",
    "PredictionInterface",
    "BitcoinDataLoader",
    "PredictionStorage"
] 