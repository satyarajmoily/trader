"""Simple keyword-based Bitcoin price prediction logic."""

import logging
from typing import Literal

logger = logging.getLogger(__name__)

PredictionResult = Literal["up", "down"]


def predict(summary: str) -> PredictionResult:
    """
    Make a simple Bitcoin price prediction based on keyword analysis.
    
    This is the core prediction function that will be improved by the agent.
    Initial implementation uses basic keyword matching.
    
    Args:
        summary: Text summary to analyze for prediction signals
        
    Returns:
        "up" if prediction is bullish, "down" if bearish
    """
    summary_lower = summary.lower()
    
    # Bullish keywords
    bullish_signals = [
        "rate cut", "rate cuts", "lower rates",
        "adoption", "institutional", "etf approval",
        "bull", "bullish", "positive", "rally",
        "breakout", "support", "buy", "accumulate"
    ]
    
    # Bearish keywords  
    bearish_signals = [
        "rate hike", "rate hikes", "higher rates", "fed raises",
        "regulation", "ban", "crackdown", "restriction",
        "bear", "bearish", "negative", "sell", "dump",
        "resistance", "break down", "crash", "correction"
    ]
    
    # Count signal strength
    bullish_count = sum(1 for signal in bullish_signals if signal in summary_lower)
    bearish_count = sum(1 for signal in bearish_signals if signal in summary_lower)
    
    logger.info(f"Prediction analysis: {bullish_count} bullish signals, {bearish_count} bearish signals")
    
    # Make prediction based on signal strength
    if bullish_count > bearish_count:
        prediction = "up"
    elif bearish_count > bullish_count:
        prediction = "down"
    else:
        # Default to bearish when uncertain (conservative approach)
        prediction = "down"
    
    logger.info(f"Prediction for '{summary}': {prediction}")
    return prediction


if __name__ == "__main__":
    # Simple test cases
    test_cases = [
        "Fed announces rate cut to boost economy",
        "Central bank raises interest rates by 0.75%", 
        "Major institution adopts Bitcoin for treasury",
        "Government considers crypto regulation crackdown",
        "Market shows strong bullish momentum"
    ]
    
    for test in test_cases:
        result = predict(test)
        print(f"Input: {test}")
        print(f"Prediction: {result}")
        print("-" * 50) 