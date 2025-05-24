"""CoinGecko API integration tool for Bitcoin price data."""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class CoinGeckoAPI:
    """CoinGecko API client with rate limiting and error handling."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize CoinGecko API client.
        
        Args:
            api_key: Optional API key for higher rate limits
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
            
        Raises:
            requests.RequestException: For API errors
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
    
    def get_current_bitcoin_price(self) -> Dict:
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
            
            logger.info(f"Current Bitcoin price: ${result['price']:,.2f}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to fetch current Bitcoin price: {e}")
            raise
    
    def get_bitcoin_price_history(self, days: int = 30) -> List[Dict]:
        """
        Get Bitcoin price history for the specified number of days.
        
        Args:
            days: Number of days of history to fetch (max 365 for free tier)
            
        Returns:
            List of dicts with date, price, market_cap, volume
        """
        try:
            data = self._make_request(
                "coins/bitcoin/market_chart",
                params={
                    "vs_currency": "usd",
                    "days": str(days),
                    "interval": "daily"
                }
            )
            
            prices = data["prices"]
            market_caps = data["market_caps"]
            volumes = data["total_volumes"]
            
            # Combine data into structured format
            history = []
            for i, (timestamp, price) in enumerate(prices):
                date = datetime.fromtimestamp(timestamp / 1000).strftime("%Y-%m-%d")
                
                history.append({
                    "date": date,
                    "price": price,
                    "market_cap": market_caps[i][1] if i < len(market_caps) else None,
                    "volume": volumes[i][1] if i < len(volumes) else None
                })
            
            logger.info(f"Fetched {len(history)} days of Bitcoin price history")
            return history
            
        except Exception as e:
            logger.error(f"Failed to fetch Bitcoin price history: {e}")
            raise
    
    def get_bitcoin_price_at_date(self, target_date: datetime) -> Optional[Dict]:
        """
        Get Bitcoin price for a specific date.
        
        Args:
            target_date: Date to fetch price for
            
        Returns:
            Dict with price data for that date, or None if not found
        """
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
            
            if "market_data" not in data:
                logger.warning(f"No market data found for date: {date_str}")
                return None
            
            market_data = data["market_data"]
            
            result = {
                "date": target_date.strftime("%Y-%m-%d"),
                "price": market_data["current_price"]["usd"],
                "market_cap": market_data["market_cap"]["usd"],
                "volume": market_data["total_volume"]["usd"],
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Bitcoin price on {date_str}: ${result['price']:,.2f}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to fetch Bitcoin price for date {target_date}: {e}")
            return None


def get_coingecko_client(api_key: Optional[str] = None) -> CoinGeckoAPI:
    """
    Factory function to create CoinGecko API client.
    
    Args:
        api_key: Optional API key for higher rate limits
        
    Returns:
        Configured CoinGeckoAPI instance
    """
    return CoinGeckoAPI(api_key=api_key)


# Convenience functions for common operations
def fetch_current_bitcoin_price(api_key: Optional[str] = None) -> Dict:
    """Fetch current Bitcoin price using CoinGecko API."""
    client = get_coingecko_client(api_key)
    return client.get_current_bitcoin_price()


def fetch_bitcoin_history(days: int = 30, api_key: Optional[str] = None) -> List[Dict]:
    """Fetch Bitcoin price history using CoinGecko API."""
    client = get_coingecko_client(api_key)
    return client.get_bitcoin_price_history(days)


def fetch_bitcoin_price_for_date(target_date: datetime, api_key: Optional[str] = None) -> Optional[Dict]:
    """Fetch Bitcoin price for a specific date using CoinGecko API."""
    client = get_coingecko_client(api_key)
    return client.get_bitcoin_price_at_date(target_date)


if __name__ == "__main__":
    # Test the CoinGecko integration
    print("Testing CoinGecko API Integration")
    print("=" * 40)
    
    try:
        # Test current price
        print("Fetching current Bitcoin price...")
        current = fetch_current_bitcoin_price()
        print(f"Current Price: ${current['price']:,.2f}")
        print(f"24h Change: {current['change_24h']:+.2f}%")
        print(f"Volume: ${current['volume_24h']:,.0f}")
        
        print("\n" + "-" * 30)
        
        # Test price history
        print("Fetching recent price history (7 days)...")
        history = fetch_bitcoin_history(7)
        print(f"Historical data points: {len(history)}")
        if history:
            latest = history[-1]
            print(f"Latest historical price: ${latest['price']:,.2f} ({latest['date']})")
        
        print("\n" + "-" * 30)
        
        # Test specific date
        yesterday = datetime.now() - timedelta(days=1)
        print(f"Fetching price for {yesterday.strftime('%Y-%m-%d')}...")
        price_data = fetch_bitcoin_price_for_date(yesterday)
        if price_data:
            print(f"Price on {price_data['date']}: ${price_data['price']:,.2f}")
        
        print("\n" + "=" * 40)
        print("✅ CoinGecko API integration test successful!")
        
    except Exception as e:
        print(f"❌ CoinGecko API integration test failed: {e}") 