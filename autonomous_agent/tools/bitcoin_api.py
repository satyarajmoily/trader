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