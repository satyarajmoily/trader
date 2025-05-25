"""Bitcoin data loading utilities."""

import csv
import logging
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime

from .interfaces import DataLoaderInterface
from .models import OHLCVData
from .config import TIMEFRAME_CONFIG

logger = logging.getLogger(__name__)


class BitcoinDataLoader(DataLoaderInterface):
    """Loads Bitcoin OHLCV data from various sources with configurable timeframes."""
    
    def __init__(self, default_source: str = "mock_bitcoin_data.csv"):
        """Initialize with default data source."""
        self.default_source = default_source
        self._bitcoin_api = None  # Lazy initialization
    
    def load_data(self, source: str = None, timeframe: str = "1d") -> List[OHLCVData]:
        """
        Load Bitcoin OHLCV data from various sources with configurable timeframes.
        
        Args:
            source: Path to CSV file with Bitcoin data (uses default if None)
            timeframe: Time interval for data (1m, 5m, 15m, 1h, 4h, 1d)
            
        Returns:
            List of OHLCVData objects
        """
        # For backward compatibility, if source is specified, use CSV
        if source:
            try:
                return self._load_from_csv(source)
            except Exception as e:
                logger.error(f"Error loading Bitcoin data from {source}: {e}")
                return []
        
        # Use API data based on timeframe
        try:
            return self._load_from_api(timeframe)
        except Exception as e:
            logger.warning(f"Failed to load API data, falling back to CSV: {e}")
            try:
                return self._load_from_csv(self.default_source)
            except Exception as csv_error:
                logger.error(f"Error loading fallback CSV data: {csv_error}")
                return []
    
    def _load_from_csv(self, csv_file: str) -> List[OHLCVData]:
        """Load data from CSV file."""
        data = []
        csv_path = Path(csv_file)
        
        if not csv_path.exists():
            raise FileNotFoundError(f"Data file not found: {csv_file}")
        
        with open(csv_path, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    ohlcv = OHLCVData.from_dict(row)
                    data.append(ohlcv)
                except (KeyError, ValueError) as e:
                    logger.warning(f"Skipping invalid row in {csv_file}: {e}")
                    continue
        
        logger.info(f"Loaded {len(data)} days of Bitcoin price data from {csv_file}")
        return data
    
    def validate_data(self, data: List[OHLCVData]) -> bool:
        """Validate loaded data quality."""
        if not data:
            return False
        
        # Check for minimum required data points
        if len(data) < 5:
            logger.warning("Insufficient data points for analysis (minimum 5 required)")
            return False
        
        # Check for valid price data
        for ohlcv in data:
            if any(price <= 0 for price in [ohlcv.open, ohlcv.high, ohlcv.low, ohlcv.close]):
                logger.warning(f"Invalid price data found for date {ohlcv.date}")
                return False
            
            if ohlcv.volume < 0:
                logger.warning(f"Invalid volume data found for date {ohlcv.date}")
                return False
        
        return True
    
    def _get_bitcoin_api(self):
        """Get Bitcoin API instance (lazy initialization to avoid circular imports)."""
        if self._bitcoin_api is None:
            try:
                # Import here to avoid circular import
                import sys
                import os
                sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
                from autonomous_agent.tools.bitcoin_api import BitcoinPriceTool
                self._bitcoin_api = BitcoinPriceTool()
            except ImportError:
                logger.warning("Bitcoin API tool not available, using CSV fallback")
                self._bitcoin_api = None
        return self._bitcoin_api
    
    def _load_from_api(self, timeframe: str) -> List[OHLCVData]:
        """Load data from Bitcoin API based on timeframe."""
        if timeframe not in TIMEFRAME_CONFIG:
            raise ValueError(f"Unsupported timeframe: {timeframe}")
        
        config = TIMEFRAME_CONFIG[timeframe]
        bitcoin_api = self._get_bitcoin_api()
        
        if bitcoin_api is None:
            raise ValueError("Bitcoin API not available")
        
        # Get required data points and interval
        data_points_needed = config["data_points_needed"]
        api_interval = config["coingecko_interval"]
        
        # Calculate days needed based on interval
        if timeframe in ["1m", "5m", "15m"]:
            # For minute intervals, we need fewer days but more data points per day
            days = max(1, data_points_needed // (24 * 60 // int(timeframe[:-1])))
        elif timeframe in ["1h", "4h"]:
            # For hourly intervals
            hours_per_day = 24 // (4 if timeframe == "4h" else 1)
            days = max(1, data_points_needed // hours_per_day)
        else:
            # For daily intervals
            days = data_points_needed
        
        # Limit days for API constraints
        days = min(days, 365)  # CoinGecko limit
        
        logger.info(f"Fetching {days} days of {timeframe} data from API...")
        
        # Fetch historical OHLCV data
        api_data = bitcoin_api.get_historical_ohlcv(days=days, interval=api_interval)
        
        if not api_data:
            raise ValueError("No data returned from API")
        
        # Convert API data to OHLCVData objects
        ohlcv_data = []
        for data_point in api_data:
            try:
                # Convert to format expected by OHLCVData
                ohlcv = OHLCVData(
                    date=data_point["timestamp"][:10],  # Extract date part
                    open=float(data_point["open"]),
                    high=float(data_point["high"]),
                    low=float(data_point["low"]),
                    close=float(data_point["close"]),
                    volume=float(data_point.get("volume", 0))
                )
                ohlcv_data.append(ohlcv)
            except (KeyError, ValueError) as e:
                logger.warning(f"Skipping invalid API data point: {e}")
                continue
        
        # Sort by date and limit to required data points
        ohlcv_data.sort(key=lambda x: x.date)
        ohlcv_data = ohlcv_data[-data_points_needed:]  # Take most recent data
        
        logger.info(f"Loaded {len(ohlcv_data)} {timeframe} data points from API")
        return ohlcv_data
    
    def get_timeframe_info(self, timeframe: str) -> Dict:
        """Get information about a timeframe configuration."""
        if timeframe not in TIMEFRAME_CONFIG:
            return {}
        return TIMEFRAME_CONFIG[timeframe].copy()
    
    def get_supported_timeframes(self) -> List[str]:
        """Get list of supported timeframes."""
        return list(TIMEFRAME_CONFIG.keys()) 