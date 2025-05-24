"""Unit tests for CoinGecko API integration."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from tools.coingecko_tool import (
    CoinGeckoAPI,
    fetch_current_bitcoin_price,
    fetch_bitcoin_history,
    fetch_bitcoin_price_for_date
)


class TestCoinGeckoAPI:
    """Test cases for CoinGeckoAPI class."""
    
    def test_init(self):
        """Test API initialization."""
        api = CoinGeckoAPI()
        assert api.base_url == "https://api.coingecko.com/api/v3"
        assert api.rate_limit_delay == 1.0
        assert api.last_request_time == 0
    
    def test_init_with_api_key(self):
        """Test API initialization with API key."""
        api = CoinGeckoAPI(api_key="test-key")
        assert api.api_key == "test-key"
        assert "x-cg-demo-api-key" in api.session.headers
    
    @patch('tools.coingecko_tool.time.sleep')
    def test_rate_limiting(self, mock_sleep):
        """Test rate limiting functionality."""
        api = CoinGeckoAPI()
        api.last_request_time = 0
        
        # First call should not sleep
        api._rate_limit()
        mock_sleep.assert_not_called()
        
        # Second call should sleep
        api._rate_limit()
        mock_sleep.assert_called_once()
    
    @patch('tools.coingecko_tool.requests.Session.get')
    def test_successful_request(self, mock_get):
        """Test successful API request."""
        mock_response = Mock()
        mock_response.json.return_value = {"bitcoin": {"usd": 50000}}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        api = CoinGeckoAPI()
        result = api._make_request("test-endpoint")
        
        assert result == {"bitcoin": {"usd": 50000}}
        mock_get.assert_called_once()
    
    @patch('tools.coingecko_tool.requests.Session.get')
    def test_failed_request(self, mock_get):
        """Test failed API request."""
        mock_get.side_effect = Exception("Network error")
        
        api = CoinGeckoAPI()
        
        with pytest.raises(Exception):
            api._make_request("test-endpoint")
    
    @patch.object(CoinGeckoAPI, '_make_request')
    def test_get_current_bitcoin_price(self, mock_request):
        """Test fetching current Bitcoin price."""
        mock_request.return_value = {
            "bitcoin": {
                "usd": 50000,
                "usd_market_cap": 1000000000,
                "usd_24h_vol": 30000000,
                "usd_24h_change": 2.5,
                "last_updated_at": 1640995200
            }
        }
        
        api = CoinGeckoAPI()
        result = api.get_current_bitcoin_price()
        
        assert result["price"] == 50000
        assert result["market_cap"] == 1000000000
        assert result["volume_24h"] == 30000000
        assert result["change_24h"] == 2.5
        assert "last_updated" in result
        assert "timestamp" in result
    
    @patch.object(CoinGeckoAPI, '_make_request')
    def test_get_bitcoin_price_history(self, mock_request):
        """Test fetching Bitcoin price history."""
        mock_request.return_value = {
            "prices": [[1640995200000, 50000], [1641081600000, 51000]],
            "market_caps": [[1640995200000, 1000000000], [1641081600000, 1100000000]],
            "total_volumes": [[1640995200000, 30000000], [1641081600000, 35000000]]
        }
        
        api = CoinGeckoAPI()
        result = api.get_bitcoin_price_history(7)
        
        assert len(result) == 2
        assert result[0]["price"] == 50000
        assert result[1]["price"] == 51000
        assert "date" in result[0]
        assert "market_cap" in result[0]
        assert "volume" in result[0]
    
    @patch.object(CoinGeckoAPI, '_make_request')
    def test_get_bitcoin_price_at_date(self, mock_request):
        """Test fetching Bitcoin price for specific date."""
        mock_request.return_value = {
            "market_data": {
                "current_price": {"usd": 50000},
                "market_cap": {"usd": 1000000000},
                "total_volume": {"usd": 30000000}
            }
        }
        
        api = CoinGeckoAPI()
        target_date = datetime(2022, 1, 1)
        result = api.get_bitcoin_price_at_date(target_date)
        
        assert result["price"] == 50000
        assert result["market_cap"] == 1000000000
        assert result["volume"] == 30000000
        assert result["date"] == "2022-01-01"
    
    @patch.object(CoinGeckoAPI, '_make_request')
    def test_get_bitcoin_price_at_date_no_data(self, mock_request):
        """Test fetching Bitcoin price when no data available."""
        mock_request.return_value = {}
        
        api = CoinGeckoAPI()
        target_date = datetime(2022, 1, 1)
        result = api.get_bitcoin_price_at_date(target_date)
        
        assert result is None


class TestConvenienceFunctions:
    """Test cases for convenience functions."""
    
    @patch('tools.coingecko_tool.CoinGeckoAPI')
    def test_fetch_current_bitcoin_price(self, mock_api_class):
        """Test convenience function for current price."""
        mock_api = Mock()
        mock_api.get_current_bitcoin_price.return_value = {"price": 50000}
        mock_api_class.return_value = mock_api
        
        result = fetch_current_bitcoin_price()
        
        assert result == {"price": 50000}
        mock_api.get_current_bitcoin_price.assert_called_once()
    
    @patch('tools.coingecko_tool.CoinGeckoAPI')
    def test_fetch_bitcoin_history(self, mock_api_class):
        """Test convenience function for price history."""
        mock_api = Mock()
        mock_api.get_bitcoin_price_history.return_value = [{"price": 50000}]
        mock_api_class.return_value = mock_api
        
        result = fetch_bitcoin_history(7)
        
        assert result == [{"price": 50000}]
        mock_api.get_bitcoin_price_history.assert_called_once_with(7)
    
    @patch('tools.coingecko_tool.CoinGeckoAPI')
    def test_fetch_bitcoin_price_for_date(self, mock_api_class):
        """Test convenience function for specific date price."""
        mock_api = Mock()
        mock_api.get_bitcoin_price_at_date.return_value = {"price": 50000}
        mock_api_class.return_value = mock_api
        
        target_date = datetime(2022, 1, 1)
        result = fetch_bitcoin_price_for_date(target_date)
        
        assert result == {"price": 50000}
        mock_api.get_bitcoin_price_at_date.assert_called_once_with(target_date) 