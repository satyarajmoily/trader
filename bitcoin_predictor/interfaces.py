"""Interfaces for the Bitcoin prediction system."""

from abc import ABC, abstractmethod
from typing import List, Optional
from .models import PredictionRecord, OHLCVData, AnalysisResult, PredictionResult


class PredictionInterface(ABC):
    """Abstract interface for Bitcoin prediction systems."""
    
    @abstractmethod
    def predict(self, data_source: Optional[str] = None) -> PredictionRecord:
        """Make a Bitcoin price prediction."""
        pass
    
    @abstractmethod
    def analyze(self, price_data: List[OHLCVData]) -> AnalysisResult:
        """Analyze price data and return technical analysis."""
        pass
    
    @abstractmethod
    def get_prediction_history(self, limit: Optional[int] = None) -> List[PredictionRecord]:
        """Get historical predictions."""
        pass


class DataLoaderInterface(ABC):
    """Abstract interface for data loading."""
    
    @abstractmethod
    def load_data(self, source: str) -> List[OHLCVData]:
        """Load Bitcoin OHLCV data from source."""
        pass


class StorageInterface(ABC):
    """Abstract interface for prediction storage."""
    
    @abstractmethod
    def save_prediction(self, prediction: PredictionRecord) -> bool:
        """Save a prediction record."""
        pass
    
    @abstractmethod
    def load_predictions(self) -> List[PredictionRecord]:
        """Load all prediction records."""
        pass
    
    @abstractmethod
    def update_prediction(self, prediction_id: str, updates: dict) -> bool:
        """Update an existing prediction record."""
        pass 