"""Configuration for the standalone Bitcoin predictor system."""

import logging
import os
from pathlib import Path


class PredictorConfig:
    """Configuration for the Bitcoin predictor system."""
    
    # Data sources
    DEFAULT_DATA_SOURCE = "mock_bitcoin_data.csv"
    PREDICTIONS_LOG_FILE = "predictions_log.json"
    
    # Logging configuration
    LOG_LEVEL = os.getenv("PREDICTOR_LOG_LEVEL", "INFO")
    LOG_FILE = "predictor.log"
    
    # Analysis parameters
    SHORT_MA_DAYS = int(os.getenv("SHORT_MA_DAYS", "3"))
    LONG_MA_DAYS = int(os.getenv("LONG_MA_DAYS", "5"))
    MOMENTUM_THRESHOLD = float(os.getenv("MOMENTUM_THRESHOLD", "0.02"))
    VOLUME_THRESHOLD = float(os.getenv("VOLUME_THRESHOLD", "1.1"))
    
    # Prediction thresholds
    BULLISH_THRESHOLD_HIGH = float(os.getenv("BULLISH_THRESHOLD_HIGH", "2.0"))
    BULLISH_THRESHOLD_LOW = float(os.getenv("BULLISH_THRESHOLD_LOW", "1.5"))
    
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