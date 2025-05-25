"""Configuration for the standalone Bitcoin predictor system."""

import logging
import os
from pathlib import Path
from typing import Dict, Any, List
from enum import Enum


class TimeInterval(Enum):
    """Supported time intervals for predictions."""
    ONE_MINUTE = "1m"
    FIVE_MINUTES = "5m"
    FIFTEEN_MINUTES = "15m"
    ONE_HOUR = "1h"
    FOUR_HOURS = "4h"
    ONE_DAY = "1d"


# Timeframe configuration mapping
TIMEFRAME_CONFIG: Dict[str, Dict[str, Any]] = {
    "1m": {
        "short_ma_periods": 3,        # 3-minute moving average
        "long_ma_periods": 5,         # 5-minute moving average  
        "momentum_periods": 5,        # 5-minute momentum
        "volume_periods": 10,         # 10-minute volume analysis
        "eval_after_minutes": 2,      # Evaluate after 2 minutes
        "data_points_needed": 10,     # Need 10 minutes of data
        "coingecko_interval": "1",    # 1-minute data from API
        "display_name": "1 minute",
        "short_name": "1m"
    },
    "5m": {
        "short_ma_periods": 3,        # 3 * 5-minute = 15-minute MA
        "long_ma_periods": 5,         # 5 * 5-minute = 25-minute MA
        "momentum_periods": 5,        # 25-minute momentum
        "volume_periods": 8,          # 8 * 5-minute = 40-minute volume analysis
        "eval_after_minutes": 10,     # Evaluate after 10 minutes
        "data_points_needed": 10,     # Need 50 minutes of data
        "coingecko_interval": "5",
        "display_name": "5 minutes",
        "short_name": "5m"
    },
    "15m": {
        "short_ma_periods": 3,        # 3 * 15-minute = 45-minute MA
        "long_ma_periods": 5,         # 5 * 15-minute = 75-minute MA
        "momentum_periods": 5,        # 75-minute momentum
        "volume_periods": 8,          # 8 * 15-minute = 2-hour volume analysis
        "eval_after_minutes": 30,     # Evaluate after 30 minutes
        "data_points_needed": 10,     # Need 150 minutes of data
        "coingecko_interval": "15",
        "display_name": "15 minutes",
        "short_name": "15m"
    },
    "1h": {
        "short_ma_periods": 3,        # 3-hour MA
        "long_ma_periods": 5,         # 5-hour MA
        "momentum_periods": 5,        # 5-hour momentum
        "volume_periods": 10,         # 10-hour volume analysis  
        "eval_after_minutes": 120,    # Evaluate after 2 hours
        "data_points_needed": 10,     # Need 10 hours of data
        "coingecko_interval": "hourly",
        "display_name": "1 hour",
        "short_name": "1h"
    },
    "4h": {
        "short_ma_periods": 3,        # 3 * 4-hour = 12-hour MA
        "long_ma_periods": 5,         # 5 * 4-hour = 20-hour MA
        "momentum_periods": 5,        # 20-hour momentum
        "volume_periods": 8,          # 8 * 4-hour = 32-hour volume analysis
        "eval_after_minutes": 480,    # Evaluate after 8 hours
        "data_points_needed": 10,     # Need 40 hours of data
        "coingecko_interval": "4h",
        "display_name": "4 hours",
        "short_name": "4h"
    },
    "1d": {
        "short_ma_periods": 3,        # 3-day MA (current default)
        "long_ma_periods": 5,         # 5-day MA (current default)
        "momentum_periods": 5,        # 5-day momentum (current default)
        "volume_periods": 30,         # 30-day volume analysis (current default)
        "eval_after_minutes": 1440,   # Evaluate after 24 hours
        "data_points_needed": 30,     # Need 30 days (current default)
        "coingecko_interval": "daily",
        "display_name": "1 day",
        "short_name": "1d"
    }
}


class PredictorConfig:
    """Configuration for the Bitcoin predictor system."""
    
    # Data sources
    DEFAULT_DATA_SOURCE = "mock_bitcoin_data.csv"
    PREDICTIONS_LOG_FILE = "predictions_log.json"
    
    # Logging configuration
    LOG_LEVEL = os.getenv("PREDICTOR_LOG_LEVEL", "INFO")
    LOG_FILE = "predictor.log"
    
    # Default timeframe (backward compatibility)
    DEFAULT_TIMEFRAME = os.getenv("DEFAULT_TIMEFRAME", "1d")
    
    # Legacy analysis parameters (for backward compatibility)
    SHORT_MA_DAYS = int(os.getenv("SHORT_MA_DAYS", "3"))
    LONG_MA_DAYS = int(os.getenv("LONG_MA_DAYS", "5"))
    MOMENTUM_THRESHOLD = float(os.getenv("MOMENTUM_THRESHOLD", "0.02"))
    VOLUME_THRESHOLD = float(os.getenv("VOLUME_THRESHOLD", "1.1"))
    
    # Prediction thresholds
    BULLISH_THRESHOLD_HIGH = float(os.getenv("BULLISH_THRESHOLD_HIGH", "2.0"))
    BULLISH_THRESHOLD_LOW = float(os.getenv("BULLISH_THRESHOLD_LOW", "1.5"))
    
    @classmethod
    def get_timeframe_config(cls, timeframe: str = None) -> Dict[str, Any]:
        """Get configuration for a specific timeframe."""
        if timeframe is None:
            timeframe = cls.DEFAULT_TIMEFRAME
        
        if timeframe not in TIMEFRAME_CONFIG:
            raise ValueError(f"Unsupported timeframe: {timeframe}. Supported: {list(TIMEFRAME_CONFIG.keys())}")
        
        return TIMEFRAME_CONFIG[timeframe].copy()
    
    @classmethod
    def get_supported_timeframes(cls) -> List[str]:
        """Get list of supported timeframes."""
        return list(TIMEFRAME_CONFIG.keys())
    
    @classmethod
    def validate_timeframe(cls, timeframe: str) -> bool:
        """Validate if timeframe is supported."""
        return timeframe in TIMEFRAME_CONFIG
    
    @classmethod
    def setup_logging(cls):
        """Setup logging configuration."""
        logging.basicConfig(
            level=getattr(logging, cls.LOG_LEVEL.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(cls.LOG_FILE)
            ]
        )
    
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration."""
        # Check if data file exists
        data_file = Path(cls.DEFAULT_DATA_SOURCE)
        if not data_file.exists():
            print(f"Warning: Default data file not found: {cls.DEFAULT_DATA_SOURCE}")
            return False
        
        # Validate parameters
        if cls.SHORT_MA_DAYS >= cls.LONG_MA_DAYS:
            print("Error: SHORT_MA_DAYS must be less than LONG_MA_DAYS")
            return False
        
        return True


# Global config instance
config = PredictorConfig() 