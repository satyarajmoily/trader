"""Bitcoin API integration for the autonomous agent system."""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class BitcoinPriceTool:
    """Bitcoin price data tool using CoinGecko API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Bitcoin price tool.
        
        Args:
            api_key: Optional CoinGecko API key for higher rate limits
        """
        self.base_url = "https://api.coingecko.com/api/v3"
        self.api_key = api_key
        self.session = self._create_session()
        self.rate_limit_delay = 1.0  # Seconds between requests
        self.last_request_time = 0
        
    def _create_session(self) -> requests.Session:
        """Create requests session with retry strategy."""
        session = requests.Session()
        
        # Retry strategy for network issues
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set headers
        session.headers.update({
            "User-Agent": "Bitcoin-Predictor-Agent/1.0",
            "Accept": "application/json"
        })
        
        if self.api_key:
            session.headers.update({"x-cg-demo-api-key": self.api_key})
            
        return session
    
    def _rate_limit(self):
        """Implement rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
            
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """
        Make rate-limited request to CoinGecko API.
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            
        Returns:
            JSON response data
        """
        self._rate_limit()
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            logger.debug(f"CoinGecko API request successful: {endpoint}")
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"CoinGecko API request failed: {endpoint} - {e}")
            raise
    
    def get_current_price(self) -> Dict:
        """
        Get current Bitcoin price data.
        
        Returns:
            Dict with current price, market cap, volume, and timestamp
        """
        try:
            data = self._make_request(
                "simple/price",
                params={
                    "ids": "bitcoin",
                    "vs_currencies": "usd",
                    "include_market_cap": "true",
                    "include_24hr_vol": "true",
                    "include_24hr_change": "true",
                    "include_last_updated_at": "true"
                }
            )
            
            bitcoin_data = data["bitcoin"]
            
            result = {
                "price": bitcoin_data["usd"],
                "market_cap": bitcoin_data["usd_market_cap"],
                "volume_24h": bitcoin_data["usd_24h_vol"],
                "change_24h": bitcoin_data["usd_24h_change"],
                "last_updated": datetime.fromtimestamp(
                    bitcoin_data["last_updated_at"]
                ).isoformat(),
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Current Bitcoin price: ${result['price']:,.2f} ({result['change_24h']:+.2f}%)")
            return result
            
        except Exception as e:
            logger.error(f"Failed to fetch current Bitcoin price: {e}")
            raise
    
    def get_price_at_timestamp(self, timestamp: str) -> Optional[Dict]:
        """
        Get Bitcoin price at a specific timestamp (24 hours later).
        
        Args:
            timestamp: ISO timestamp to get price for (adds 24h)
            
        Returns:
            Dict with price data or None if not available
        """
        try:
            # Parse the prediction timestamp and add 24 hours
            pred_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            target_time = pred_time + timedelta(hours=24)
            
            # If target time is in the future, get current price
            if target_time > datetime.now():
                logger.info("Target time is in future, returning current price")
                return self.get_current_price()
            
            # For historical data, use the history API
            return self._get_historical_price(target_time)
            
        except Exception as e:
            logger.error(f"Failed to get price at timestamp {timestamp}: {e}")
            return None
    
    def _get_historical_price(self, target_date: datetime) -> Optional[Dict]:
        """Get historical Bitcoin price for a specific date."""
        try:
            # Format date for API
            date_str = target_date.strftime("%d-%m-%Y")
            
            data = self._make_request(
                "coins/bitcoin/history",
                params={
                    "date": date_str,
                    "localization": "false"
                }
            )
            
            if "market_data" in data and data["market_data"]:
                market_data = data["market_data"]
                price = market_data["current_price"]["usd"]
                
                result = {
                    "price": price,
                    "date": target_date.strftime("%Y-%m-%d"),
                    "timestamp": target_date.isoformat()
                }
                
                logger.info(f"Historical Bitcoin price on {date_str}: ${price:,.2f}")
                return result
            
            logger.warning(f"No market data found for date {date_str}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to fetch historical price for {target_date}: {e}")
            return None
    
    def determine_price_movement(self, initial_price: float, final_price: float) -> str:
        """
        Determine if price movement was up or down.
        
        Args:
            initial_price: Starting price
            final_price: Ending price
            
        Returns:
            "up" if price increased, "down" if decreased
        """
        return "up" if final_price > initial_price else "down"
    
    def calculate_price_change(self, initial_price: float, final_price: float) -> Dict:
        """
        Calculate price change metrics.
        
        Args:
            initial_price: Starting price
            final_price: Ending price
            
        Returns:
            Dict with change amount and percentage
        """
        change_amount = final_price - initial_price
        change_percent = (change_amount / initial_price) * 100
        
        return {
            "initial_price": initial_price,
            "final_price": final_price,
            "change_amount": change_amount,
            "change_percent": change_percent,
            "direction": self.determine_price_movement(initial_price, final_price)
        }
    
    def get_historical_ohlcv(self, days: int = 30, interval: str = "daily") -> List[Dict]:
        """
        Get historical OHLCV data for different time intervals.
        
        Args:
            days: Number of days of historical data
            interval: Data interval ("1", "5", "15", "hourly", "daily")
            
        Returns:
            List of OHLCV data points
        """
        try:
            # Map intervals to CoinGecko API parameters
            interval_mapping = {
                "1": "1",      # 1-minute (requires Pro API)
                "5": "5",      # 5-minute (requires Pro API)
                "15": "15",    # 15-minute (requires Pro API)
                "hourly": "hourly",
                "daily": "daily"
            }
            
            if interval not in interval_mapping:
                raise ValueError(f"Unsupported interval: {interval}")
            
            # For minute/hour intervals, we need the market_chart API
            if interval in ["1", "5", "15", "hourly"]:
                return self._get_intraday_ohlcv(days, interval)
            else:
                return self._get_daily_ohlcv(days)
                
        except Exception as e:
            logger.error(f"Failed to fetch historical OHLCV data: {e}")
            raise
    
    def _get_intraday_ohlcv(self, days: int, interval: str) -> List[Dict]:
        """Get intraday OHLCV data (requires processing from market_chart)."""
        try:
            # CoinGecko free API limitations for intraday data
            if days > 1 and interval in ["1", "5", "15"]:
                logger.warning(f"Minute-level data limited to 1 day on free tier, adjusting days to 1")
                days = 1
            
            data = self._make_request(
                "coins/bitcoin/market_chart",
                params={
                    "vs_currency": "usd",
                    "days": str(days),
                    "interval": interval if interval != "hourly" else "hourly"
                }
            )
            
            prices = data.get("prices", [])
            market_caps = data.get("market_caps", [])
            total_volumes = data.get("total_volumes", [])
            
            # Convert to OHLCV format (simplified - using price as OHLC)
            ohlcv_data = []
            for i, (timestamp, price) in enumerate(prices):
                # Get corresponding volume
                volume = total_volumes[i][1] if i < len(total_volumes) else 0
                market_cap = market_caps[i][1] if i < len(market_caps) else 0
                
                ohlcv_data.append({
                    "timestamp": datetime.fromtimestamp(timestamp / 1000).isoformat(),
                    "open": price,    # Simplified: using same price for OHLC
                    "high": price,
                    "low": price,
                    "close": price,
                    "volume": volume,
                    "market_cap": market_cap
                })
            
            logger.info(f"Fetched {len(ohlcv_data)} {interval} data points for {days} days")
            return ohlcv_data
            
        except Exception as e:
            logger.error(f"Failed to fetch intraday OHLCV data: {e}")
            raise
    
    def _get_daily_ohlcv(self, days: int) -> List[Dict]:
        """Get daily OHLCV data."""
        try:
            data = self._make_request(
                "coins/bitcoin/ohlc",
                params={
                    "vs_currency": "usd",
                    "days": str(days)
                }
            )
            
            ohlcv_data = []
            for ohlc in data:
                timestamp, open_price, high, low, close = ohlc
                
                ohlcv_data.append({
                    "timestamp": datetime.fromtimestamp(timestamp / 1000).isoformat(),
                    "open": open_price,
                    "high": high,
                    "low": low,
                    "close": close,
                    "volume": 0  # OHLC endpoint doesn't include volume
                })
            
            logger.info(f"Fetched {len(ohlcv_data)} daily OHLC data points for {days} days")
            return ohlcv_data
            
        except Exception as e:
            logger.error(f"Failed to fetch daily OHLCV data: {e}")
            raise
    
    def get_price_at_timestamp_with_interval(self, timestamp: str, interval: str) -> Optional[Dict]:
        """
        Get Bitcoin price at a specific timestamp with configurable interval.
        
        Args:
            timestamp: ISO timestamp of prediction
            interval: Time interval for prediction (1m, 5m, 1h, 1d, etc.)
            
        Returns:
            Dict with price data or None if not available
        """
        try:
            # Parse the prediction timestamp
            pred_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
            # Calculate target time based on interval
            interval_mapping = {
                "1m": timedelta(minutes=1),
                "5m": timedelta(minutes=5),
                "15m": timedelta(minutes=15),
                "1h": timedelta(hours=1),
                "4h": timedelta(hours=4),
                "1d": timedelta(days=1)
            }
            
            if interval not in interval_mapping:
                logger.warning(f"Unknown interval {interval}, using 24h default")
                target_time = pred_time + timedelta(hours=24)
            else:
                target_time = pred_time + interval_mapping[interval]
            
            # If target time is in the future, get current price
            if target_time > datetime.now():
                logger.info(f"Target time {target_time} is in future, returning current price")
                return self.get_current_price()
            
            # For historical data, use appropriate method based on interval
            if interval in ["1m", "5m", "15m", "1h"]:
                # For short intervals, we may need recent data
                return self._get_recent_price_data(target_time)
            else:
                # For daily intervals, use existing historical method
                return self._get_historical_price(target_time)
                
        except Exception as e:
            logger.error(f"Failed to get price at timestamp {timestamp} with interval {interval}: {e}")
            return None
    
    def _get_recent_price_data(self, target_time: datetime) -> Optional[Dict]:
        """Get recent price data for short-term intervals."""
        try:
            # For short-term data, get hourly data for the last few days
            current_time = datetime.now()
            days_back = max(1, (current_time - target_time).days + 1)
            
            # Limit to reasonable timeframe for API limits
            days_back = min(days_back, 7)
            
            hourly_data = self._get_intraday_ohlcv(days_back, "hourly")
            
            if not hourly_data:
                logger.warning("No hourly data available, falling back to current price")
                return self.get_current_price()
            
            # Find closest data point to target time
            closest_data = min(
                hourly_data,
                key=lambda x: abs(
                    datetime.fromisoformat(x["timestamp"]) - target_time
                )
            )
            
            result = {
                "price": closest_data["close"],
                "timestamp": closest_data["timestamp"],
                "source": "historical_hourly"
            }
            
            logger.info(f"Found historical price for {target_time}: ${result['price']:,.2f}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to get recent price data for {target_time}: {e}")
            return None 