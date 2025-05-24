"""Bitcoin data loading utilities."""

import csv
import logging
from pathlib import Path
from typing import List

from .interfaces import DataLoaderInterface
from .models import OHLCVData

logger = logging.getLogger(__name__)


class BitcoinDataLoader(DataLoaderInterface):
    """Loads Bitcoin OHLCV data from various sources."""
    
    def __init__(self, default_source: str = "mock_bitcoin_data.csv"):
        """Initialize with default data source."""
        self.default_source = default_source
    
    def load_data(self, source: str = None) -> List[OHLCVData]:
        """
        Load Bitcoin OHLCV data from CSV file.
        
        Args:
            source: Path to CSV file with Bitcoin data (uses default if None)
            
        Returns:
            List of OHLCVData objects
        """
        source = source or self.default_source
        
        try:
            return self._load_from_csv(source)
        except Exception as e:
            logger.error(f"Error loading Bitcoin data from {source}: {e}")
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