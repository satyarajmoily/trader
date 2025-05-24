"""Bitcoin price prediction logic using OHLCV data analysis."""

import csv
import logging
from datetime import datetime
from typing import Dict, List, Literal

logger = logging.getLogger(__name__)

PredictionResult = Literal["up", "down"]


def load_bitcoin_data(csv_file: str = "mock_bitcoin_data.csv") -> List[Dict]:
    """
    Load Bitcoin OHLCV data from CSV file.
    
    Args:
        csv_file: Path to CSV file with Bitcoin data
        
    Returns:
        List of dicts with date, open, high, low, close, volume
    """
    data = []
    try:
        with open(csv_file, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                data.append({
                    'date': row['date'],
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': int(row['volume'])
                })
        logger.info(f"Loaded {len(data)} days of Bitcoin price data")
        return data
    except Exception as e:
        logger.error(f"Error loading Bitcoin data: {e}")
        return []


def predict(price_data: List[Dict]) -> PredictionResult:
    """
    Make a Bitcoin price prediction based on OHLCV trend analysis.
    
    This is the core prediction function that will be improved by the agent.
    Initial implementation uses simple moving averages and momentum.
    
    Args:
        price_data: List of dicts with date, open, high, low, close, volume
        
    Returns:
        "up" if prediction is bullish, "down" if bearish
    """
    if not price_data or len(price_data) < 5:
        logger.warning("Insufficient price data for prediction")
        return "down"  # Conservative default
    
    # Get recent closing prices for trend analysis
    recent_closes = [day['close'] for day in price_data[-7:]]  # Last 7 days
    
    # Calculate simple moving averages
    short_ma = sum(recent_closes[-3:]) / 3  # 3-day MA
    long_ma = sum(recent_closes[-5:]) / 5   # 5-day MA
    
    # Calculate price momentum
    current_price = recent_closes[-1]
    price_5_days_ago = recent_closes[-5] if len(recent_closes) >= 5 else recent_closes[0]
    momentum = (current_price - price_5_days_ago) / price_5_days_ago
    
    # Calculate volume trend
    recent_volumes = [day['volume'] for day in price_data[-3:]]
    volume_trend = sum(recent_volumes[-2:]) / sum(recent_volumes[-3:-1]) if len(recent_volumes) >= 3 else 1.0
    
    logger.info(f"Analysis: Short MA={short_ma:.2f}, Long MA={long_ma:.2f}")
    logger.info(f"Momentum: {momentum:.4f} ({momentum*100:.2f}%)")
    logger.info(f"Volume trend: {volume_trend:.3f}")
    
    # Bullish signals
    bullish_signals = 0
    if short_ma > long_ma:  # Short MA above long MA
        bullish_signals += 1
        logger.info("✓ Bullish: Short MA > Long MA")
    
    if momentum > 0.02:  # Positive momentum > 2%
        bullish_signals += 1
        logger.info("✓ Bullish: Strong positive momentum")
    elif momentum > 0:
        bullish_signals += 0.5
        logger.info("✓ Bullish: Positive momentum")
    
    if volume_trend > 1.1:  # Increasing volume
        bullish_signals += 0.5
        logger.info("✓ Bullish: Volume increasing")
    
    # Make prediction based on signal strength
    if bullish_signals >= 2:
        prediction = "up"
    elif bullish_signals >= 1.5:
        prediction = "up"  # Lean bullish
    else:
        prediction = "down"  # Conservative default
    
    logger.info(f"Bullish signals: {bullish_signals}/3.0")
    logger.info(f"Prediction: {prediction}")
    
    return prediction


def get_latest_prediction() -> Dict:
    """
    Load latest Bitcoin data and make a prediction.
    
    Returns:
        Dict with prediction, timestamp, and analysis data
    """
    price_data = load_bitcoin_data()
    if not price_data:
        return {
            "error": "Failed to load price data",
            "timestamp": datetime.now().isoformat()
        }
    
    prediction = predict(price_data)
    latest_price = price_data[-1]['close']
    
    return {
        "prediction": prediction,
        "timestamp": datetime.now().isoformat(),
        "latest_price": latest_price,
        "data_points": len(price_data),
        "analysis_period": f"{price_data[0]['date']} to {price_data[-1]['date']}"
    }


if __name__ == "__main__":
    # Test the prediction system
    print("Bitcoin Price Prediction System")
    print("=" * 40)
    
    # Load data and make prediction
    result = get_latest_prediction()
    
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print(f"Latest Bitcoin Price: ${result['latest_price']:,.2f}")
        print(f"Data Period: {result['analysis_period']}")
        print(f"Data Points: {result['data_points']}")
        print(f"Prediction: {result['prediction'].upper()}")
        print(f"Timestamp: {result['timestamp']}")
    
    print("\n" + "=" * 40)
    print("Price-based prediction system ready!") 