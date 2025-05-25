"""Bitcoin API integration for the autonomous agent system."""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
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
        
        NOTE: CoinGecko free tier uses automatic granularity:
        - 1 day from current time = 5-minutely data
        - 2-90 days from current time = hourly data  
        - Above 90 days = daily data
        
        Args:
            days: Number of days of historical data
            interval: Data interval preference ("1m", "5m", "15m", "1h", "daily")
                     Note: Minute intervals only work with days=1 on free tier
            
        Returns:
            List of OHLCV data points with automatic granularity
        """
        try:
            # For free tier, we work with automatic granularity
            # Map user preferences to what's possible
            if interval in ["1m", "5m", "15m"]:
                if days > 1:
                    logger.info(f"Minute-level intervals require days=1 on free tier, adjusting")
                    days = 1
                return self._get_intraday_ohlcv(days, interval)
                
            elif interval in ["1h", "hourly"]:
                if days > 90:
                    logger.info(f"Hourly data limited to 90 days on free tier, adjusting")
                    days = 90
                return self._get_intraday_ohlcv(days, "hourly")
                
            elif interval == "daily":
                # For daily data, use OHLC endpoint which gives proper OHLC values
                return self._get_daily_ohlcv(days)
                
            else:
                logger.warning(f"Unknown interval '{interval}', defaulting to daily")
                return self._get_daily_ohlcv(days)
                
        except Exception as e:
            logger.error(f"Failed to fetch historical OHLCV data: {e}")
            raise
    
    def _get_intraday_ohlcv(self, days: int, interval: str) -> List[Dict]:
        """Get intraday OHLCV data using automatic granularity (free tier compatible)."""
        try:
            # Important: CoinGecko interval parameter is ONLY for Enterprise subscribers
            # For free/non-Enterprise users, we must use automatic granularity:
            # - 1 day from current time = 5-minutely data
            # - 2-90 days from current time = hourly data
            # - Above 90 days = daily data
            
            # Adjust days for automatic granularity
            if interval in ["1m", "5m", "15m"] and days > 1:
                logger.info(f"Adjusting to 1 day for {interval} granularity (free tier limitation)")
                days = 1
            elif interval == "hourly" and days > 90:
                logger.info(f"Adjusting to 90 days for hourly granularity (free tier limitation)")
                days = 90
            
            # Make request WITHOUT interval parameter (automatic granularity)
            params = {
                "vs_currency": "usd",
                "days": str(days)
            }
            
            logger.info(f"Fetching Bitcoin market chart data for {days} days (auto-granularity)")
            data = self._make_request("coins/bitcoin/market_chart", params=params)
            
            prices = data.get("prices", [])
            market_caps = data.get("market_caps", [])
            total_volumes = data.get("total_volumes", [])
            
            if not prices:
                logger.warning("No price data received from CoinGecko API")
                return []
            
            # Convert to OHLCV format (simplified - using price as OHLC)
            ohlcv_data = []
            for i, (timestamp, price) in enumerate(prices):
                # Get corresponding volume and market cap
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
            
            # Determine actual granularity received
            if len(ohlcv_data) > 1:
                time_diff = datetime.fromisoformat(ohlcv_data[1]["timestamp"]) - datetime.fromisoformat(ohlcv_data[0]["timestamp"])
                actual_interval = str(int(time_diff.total_seconds() / 60)) + "m"
                if time_diff.total_seconds() >= 3600:
                    actual_interval = str(int(time_diff.total_seconds() / 3600)) + "h"
                logger.info(f"Received {len(ohlcv_data)} data points with ~{actual_interval} granularity for {days} days")
            else:
                logger.info(f"Received {len(ohlcv_data)} data points for {days} days")
            
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
    
    def test_api_connection(self) -> Dict[str, Any]:
        """
        Test the API connection and verify no 401 errors with free tier.
        
        Returns:
            Dict with test results
        """
        try:
            results = {
                "current_price": False,
                "historical_price": False,
                "market_chart_1d": False,
                "market_chart_auto": False,
                "errors": []
            }
            
            # Test 1: Current price
            try:
                price_data = self.get_current_price()
                results["current_price"] = True
                logger.info(f"✅ Current price test passed: ${price_data['price']:,.2f}")
            except Exception as e:
                results["errors"].append(f"Current price test failed: {e}")
                logger.error(f"❌ Current price test failed: {e}")
            
            # Test 2: Historical price
            try:
                yesterday = (datetime.now() - timedelta(days=1)).isoformat()
                hist_data = self.get_price_at_timestamp(yesterday)
                if hist_data:
                    results["historical_price"] = True
                    logger.info(f"✅ Historical price test passed")
                else:
                    results["errors"].append("Historical price returned None")
            except Exception as e:
                results["errors"].append(f"Historical price test failed: {e}")
                logger.error(f"❌ Historical price test failed: {e}")
            
            # Test 3: Market chart with 1 day (should get 5-minute data)
            try:
                ohlcv_data = self.get_historical_ohlcv(days=1, interval="1m")
                if ohlcv_data and len(ohlcv_data) > 0:
                    results["market_chart_1d"] = True
                    logger.info(f"✅ Market chart 1-day test passed: {len(ohlcv_data)} data points")
                else:
                    results["errors"].append("Market chart 1-day returned no data")
            except Exception as e:
                results["errors"].append(f"Market chart 1-day test failed: {e}")
                logger.error(f"❌ Market chart 1-day test failed: {e}")
            
            # Test 4: Market chart with automatic granularity
            try:
                ohlcv_data = self.get_historical_ohlcv(days=7, interval="1h")
                if ohlcv_data and len(ohlcv_data) > 0:
                    results["market_chart_auto"] = True
                    logger.info(f"✅ Market chart auto-granularity test passed: {len(ohlcv_data)} data points")
                else:
                    results["errors"].append("Market chart auto-granularity returned no data")
            except Exception as e:
                results["errors"].append(f"Market chart auto-granularity test failed: {e}")
                logger.error(f"❌ Market chart auto-granularity test failed: {e}")
            
            # Overall success
            tests_passed = sum([results["current_price"], results["historical_price"], 
                              results["market_chart_1d"], results["market_chart_auto"]])
            results["overall_success"] = tests_passed >= 3  # At least 3 out of 4 should pass
            results["tests_passed"] = f"{tests_passed}/4"
            
            if results["overall_success"]:
                logger.info("🎉 Bitcoin API connection test PASSED - Free tier compatible!")
            else:
                logger.warning(f"⚠️ Bitcoin API test partially failed: {tests_passed}/4 tests passed")
            
            return results
            
        except Exception as e:
            logger.error(f"API connection test failed completely: {e}")
            return {
                "overall_success": False,
                "tests_passed": "0/4",
                "errors": [f"Complete test failure: {e}"]
            } 