"""Data models for the Bitcoin prediction system."""

from datetime import datetime
from typing import Dict, List, Literal, Optional
from dataclasses import dataclass, asdict
import json

# Type definitions
PredictionResult = Literal["up", "down"]


@dataclass
class OHLCVData:
    """Bitcoin OHLCV (Open, High, Low, Close, Volume) data point."""
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int

    @classmethod
    def from_dict(cls, data: Dict) -> 'OHLCVData':
        """Create OHLCVData from dictionary."""
        return cls(
            date=data['date'],
            open=float(data['open']),
            high=float(data['high']),
            low=float(data['low']),
            close=float(data['close']),
            volume=int(data['volume'])
        )

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class PredictionRecord:
    """A complete prediction record with metadata."""
    id: str
    prediction: PredictionResult
    timestamp: str
    latest_price: float
    data_points: int
    analysis_period: str
    confidence: Optional[float] = None
    timeframe: Optional[str] = "1d"  # Default to 1d for backward compatibility
    actual_outcome: Optional[str] = None
    actual_price: Optional[float] = None
    evaluation_timestamp: Optional[str] = None
    success: Optional[bool] = None

    @classmethod
    def from_dict(cls, data: Dict) -> 'PredictionRecord':
        """Create PredictionRecord from dictionary."""
        return cls(**data)

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class AnalysisResult:
    """Technical analysis result for prediction."""
    short_ma: float
    long_ma: float
    momentum: float
    volume_trend: float
    bullish_signals: float
    prediction: PredictionResult
    confidence: float
    reasoning: List[str]

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self) 