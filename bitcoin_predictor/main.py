#!/usr/bin/env python3
"""
Standalone Bitcoin Predictor CLI

This is the standalone entry point for the Bitcoin prediction system.
It works independently of any agent systems.
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

from . import BitcoinPredictor, PredictionStorage, BitcoinDataLoader


def setup_logging(level: str = "INFO"):
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('predictor.log')
        ]
    )


def cmd_predict(args):
    """Make a single Bitcoin price prediction."""
    print("🔮 Bitcoin Price Prediction")
    print("=" * 40)
    
    try:
        predictor = BitcoinPredictor()
        prediction = predictor.predict(args.data_source)
        
        print(f"✅ Prediction completed successfully!")
        print(f"📊 Prediction ID: {prediction.id}")
        print(f"💰 Latest Bitcoin Price: ${prediction.latest_price:,.2f}")
        print(f"📈 Prediction: {prediction.prediction.upper()}")
        print(f"🎯 Confidence: {prediction.confidence:.2f}" if prediction.confidence else "🎯 Confidence: N/A")
        print(f"📅 Data Period: {prediction.analysis_period}")
        print(f"📊 Data Points: {prediction.data_points}")
        print(f"⏰ Timestamp: {prediction.timestamp}")
        
        return True
        
    except Exception as e:
        print(f"❌ Prediction failed: {e}")
        return False


def cmd_history(args):
    """Show prediction history."""
    print("📊 Prediction History")
    print("=" * 50)
    
    try:
        storage = PredictionStorage()
        predictions = storage.get_recent_predictions(args.limit)
        
        if not predictions:
            print("No predictions found.")
            return True
        
        for i, pred in enumerate(predictions, 1):
            status = "✅ CORRECT" if pred.success is True else "❌ INCORRECT" if pred.success is False else "⏳ PENDING"
            
            print(f"\n{i}. Prediction {pred.id}")
            print(f"   📈 Prediction: {pred.prediction.upper()}")
            print(f"   💰 Price: ${pred.latest_price:,.2f}")
            print(f"   📅 Date: {pred.timestamp}")
            print(f"   📊 Status: {status}")
            
            if pred.actual_outcome:
                print(f"   🎯 Actual: {pred.actual_outcome.upper()} (${pred.actual_price:,.2f})")
                
        return True
        
    except Exception as e:
        print(f"❌ Failed to load history: {e}")
        return False


def cmd_analyze(args):
    """Analyze price data without making a prediction."""
    print("🔍 Bitcoin Price Analysis")
    print("=" * 40)
    
    try:
        predictor = BitcoinPredictor()
        data_loader = BitcoinDataLoader()
        
        # Load data
        price_data = data_loader.load_data(args.data_source)
        if not price_data:
            print("❌ Failed to load price data")
            return False
        
        # Perform analysis
        analysis = predictor.analyze(price_data)
        
        print(f"📊 Technical Analysis Results:")
        print(f"   📈 Short MA (3-day): ${analysis.short_ma:,.2f}")
        print(f"   📉 Long MA (5-day): ${analysis.long_ma:,.2f}")
        print(f"   ⚡ Momentum: {analysis.momentum:.4f} ({analysis.momentum*100:.2f}%)")
        print(f"   📊 Volume Trend: {analysis.volume_trend:.3f}")
        print(f"   🎯 Bullish Signals: {analysis.bullish_signals}/3.0")
        print(f"   📈 Prediction: {analysis.prediction.upper()}")
        print(f"   🎯 Confidence: {analysis.confidence:.2f}")
        
        print(f"\n🧠 Analysis Reasoning:")
        for reason in analysis.reasoning:
            print(f"   • {reason}")
        
        return True
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return False


def cmd_test(args):
    """Test the prediction system."""
    print("🧪 Testing Bitcoin Prediction System")
    print("=" * 45)
    
    success = True
    
    # Test 1: Data loading
    print("1. Testing data loading...")
    try:
        data_loader = BitcoinDataLoader()
        data = data_loader.load_data()
        if data and len(data) >= 5:
            print(f"   ✅ Loaded {len(data)} data points")
        else:
            print("   ❌ Insufficient data loaded")
            success = False
    except Exception as e:
        print(f"   ❌ Data loading failed: {e}")
        success = False
    
    print()
    
    # Test 2: Prediction
    print("2. Testing prediction...")
    try:
        predictor = BitcoinPredictor()
        prediction = predictor.predict()
        print(f"   ✅ Prediction: {prediction.prediction.upper()}")
        print(f"   ✅ Price: ${prediction.latest_price:,.2f}")
    except Exception as e:
        print(f"   ❌ Prediction failed: {e}")
        success = False
    
    print()
    
    # Test 3: Storage
    print("3. Testing storage...")
    try:
        storage = PredictionStorage()
        predictions = storage.load_predictions()
        print(f"   ✅ Loaded {len(predictions)} stored predictions")
    except Exception as e:
        print(f"   ❌ Storage test failed: {e}")
        success = False
    
    print("\n" + "=" * 45)
    if success:
        print("✅ All tests passed! Predictor system is ready.")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    
    return success


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Standalone Bitcoin Price Predictor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python predictor_main.py predict              # Make a prediction
  python predictor_main.py history              # Show prediction history  
  python predictor_main.py analyze              # Analyze price data
  python predictor_main.py test                 # Test the system
        """
    )
    
    # Global options
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level'
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Predict command
    predict_parser = subparsers.add_parser('predict', help='Make a Bitcoin price prediction')
    predict_parser.add_argument(
        '--data-source',
        help='Path to Bitcoin price data CSV file'
    )
    
    # History command
    history_parser = subparsers.add_parser('history', help='Show prediction history')
    history_parser.add_argument(
        '--limit',
        type=int,
        default=10,
        help='Maximum number of predictions to show'
    )
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze price data without prediction')
    analyze_parser.add_argument(
        '--data-source',
        help='Path to Bitcoin price data CSV file'
    )
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test the prediction system')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Check if command was provided
    if not args.command:
        parser.print_help()
        return 1
    
    # Execute command
    command_map = {
        'predict': cmd_predict,
        'history': cmd_history,
        'analyze': cmd_analyze,
        'test': cmd_test
    }
    
    try:
        success = command_map[args.command](args)
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n🛑 Operation cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 