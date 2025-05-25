"""Core Bitcoin prediction engine."""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
import uuid

from .interfaces import PredictionInterface
from .models import PredictionRecord, OHLCVData, AnalysisResult, PredictionResult
from .data_loader import BitcoinDataLoader
from .storage import PredictionStorage
from .config import PredictorConfig, TIMEFRAME_CONFIG

logger = logging.getLogger(__name__)


class BitcoinPredictor(PredictionInterface):
    """
    Core Bitcoin price prediction engine using OHLCV technical analysis.
    
    This class implements the core prediction logic that can be improved
    by external agent systems. It's designed to be standalone and independent.
    """
    
    def __init__(self, 
                 data_loader: Optional[BitcoinDataLoader] = None,
                 storage: Optional[PredictionStorage] = None,
                 timeframe: str = "1d"):
        """
        Initialize the Bitcoin predictor.
        
        Args:
            data_loader: Custom data loader (uses default if None)
            storage: Custom storage (uses default if None)
            timeframe: Time interval for predictions (1m, 5m, 15m, 1h, 4h, 1d)
        """
        self.data_loader = data_loader or BitcoinDataLoader()
        self.storage = storage or PredictionStorage()
        self.timeframe = timeframe
        self.timeframe_config = self._get_timeframe_config(timeframe)
    
    def _get_timeframe_config(self, timeframe: str) -> Dict[str, Any]:
        """Get configuration for the specified timeframe."""
        if timeframe not in TIMEFRAME_CONFIG:
            logger.warning(f"Unknown timeframe {timeframe}, using 1d default")
            timeframe = "1d"
        return TIMEFRAME_CONFIG[timeframe]
        
    def predict(self, data_source: Optional[str] = None) -> PredictionRecord:
        """
        Make a Bitcoin price prediction.
        
        Args:
            data_source: Data source path (uses default if None)
            
        Returns:
            PredictionRecord with prediction and metadata
        """
        # Load price data with timeframe
        price_data = self.data_loader.load_data(data_source, self.timeframe)
        if not price_data:
            raise ValueError("Failed to load price data for prediction")
        
        # Validate data quality
        if not self.data_loader.validate_data(price_data):
            raise ValueError("Invalid or insufficient price data")
        
        # Perform technical analysis
        analysis = self.analyze(price_data)
        
        # Create prediction record
        timestamp = datetime.now().isoformat()
        prediction_id = f"pred_{timestamp.replace(':', '').replace('-', '').replace('.', '')}"
        
        prediction_record = PredictionRecord(
            id=prediction_id,
            prediction=analysis.prediction,
            timestamp=timestamp,
            latest_price=price_data[-1].close,
            data_points=len(price_data),
            analysis_period=f"{price_data[0].date} to {price_data[-1].date}",
            confidence=analysis.confidence,
            timeframe=self.timeframe  # Add timeframe to prediction record
        )
        
        # Save prediction
        success = self.storage.save_prediction(prediction_record)
        if not success:
            logger.warning(f"Failed to save prediction {prediction_id}")
        
        logger.info(f"Generated prediction {prediction_id}: {analysis.prediction}")
        return prediction_record
    
    def analyze(self, price_data: List[OHLCVData]) -> AnalysisResult:
        """Perform technical analysis on price data."""
        # Get configurable periods from timeframe config
        short_ma_periods = self.timeframe_config["short_ma_periods"]
        long_ma_periods = self.timeframe_config["long_ma_periods"]
        momentum_periods = self.timeframe_config["momentum_periods"]
        volume_periods = self.timeframe_config.get("volume_periods", 10)  # Configurable per timeframe
        
        # Validate minimum data requirements (use only technical indicator periods, not volume)
        min_required = max(short_ma_periods, long_ma_periods, momentum_periods)
        if not price_data or len(price_data) < min_required:
            raise ValueError(f"Insufficient price data for analysis (minimum {min_required} points required for {self.timeframe})")
        
        # Extract closing prices for trend analysis
        recent_closes = [day.close for day in price_data]
        
        # Calculate exponential moving averages
        short_ma = sum(recent_closes[-short_ma_periods:]) / short_ma_periods
        long_ma = sum(recent_closes[-long_ma_periods:]) / long_ma_periods
        
        # Calculate momentum with a longer lookback period
        current_price = recent_closes[-1]
        momentum_base_price = recent_closes[-momentum_periods] if len(recent_closes) >= momentum_periods else recent_closes[0]
        momentum = (current_price - momentum_base_price) / momentum_base_price
        
        # Enhanced volume analysis
        recent_volumes = [day.volume for day in price_data[-volume_periods:]]
        if len(recent_volumes) >= 2:
            recent_avg = sum(recent_volumes) / len(recent_volumes)
            historical_avg = sum([day.volume for day in price_data[-(volume_periods + 30):-30]]) / 30 if len(price_data) > volume_periods + 30 else 1
            volume_trend = recent_avg / historical_avg
        else:
            volume_trend = 1.0
        
        # Analyze bullish signals
        bullish_signals = 0
        reasoning = []
        
        if short_ma > long_ma:
            bullish_signals += 1
            reasoning.append(f"{short_ma_periods}-period MA ({short_ma:.2f}) > {long_ma_periods}-period MA ({long_ma:.2f})")
        else:
            reasoning.append(f"{short_ma_periods}-period MA ({short_ma:.2f}) ≤ {long_ma_periods}-period MA ({long_ma:.2f})")
        
        if momentum > 0.02:
            bullish_signals += 1
            reasoning.append(f"Strong positive momentum: {momentum:.4f} ({momentum*100:.2f}%)")
        elif momentum > 0:
            bullish_signals += 0.5
            reasoning.append(f"Weak positive momentum: {momentum:.4f} ({momentum*100:.2f}%)")
        else:
            reasoning.append(f"Negative momentum: {momentum:.4f} ({momentum*100:.2f}%)")
        
        if volume_trend > 1.1:
            bullish_signals += 0.5
            reasoning.append(f"Increasing volume trend: {volume_trend:.3f}")
        else:
            reasoning.append(f"Stable/decreasing volume trend: {volume_trend:.3f}")
        
        # Make prediction based on signal strength
        if bullish_signals >= 2:
            prediction = "up"
            confidence = min(0.9, 0.6 + (bullish_signals - 2) * 0.1)
        elif bullish_signals >= 1.5:
            prediction = "up"
            confidence = 0.6
        else:
            prediction = "down"
            confidence = min(0.9, 0.7 + (2 - bullish_signals) * 0.1)
        
        reasoning.append(f"Total bullish signals: {bullish_signals}/3.0")
        reasoning.append(f"Prediction: {prediction} (confidence: {confidence:.2f})")
        
        # Log analysis details
        logger.info(f"Technical Analysis ({self.timeframe}) - MA: {short_ma:.2f}/{long_ma:.2f}, Momentum: {momentum:.4f}, Volume: {volume_trend:.3f}")
        logger.info(f"Bullish signals: {bullish_signals}/3.0 → {prediction}")
        
        return AnalysisResult(
            short_ma=short_ma,
            long_ma=long_ma,
            momentum=momentum,
            volume_trend=volume_trend,
            bullish_signals=bullish_signals,
            prediction=prediction,
            confidence=confidence,
            reasoning=reasoning
        )
    
    def get_prediction_history(self, limit: Optional[int] = None) -> List[PredictionRecord]:
        """
        Get historical predictions.
        
        Args:
            limit: Maximum number of predictions to return
            
        Returns:
            List of PredictionRecord objects
        """
        predictions = self.storage.load_predictions()
        if limit:
            return predictions[-limit:]
        return predictions 