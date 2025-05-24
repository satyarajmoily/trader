#!/usr/bin/env python3
"""
Autonomous Agent CLI

This is the entry point for the autonomous agent system that orchestrates
Bitcoin prediction evaluation and improvement.
"""

import argparse
import logging
import os
import sys
from datetime import datetime

from . import AutonomousAgent

logger = logging.getLogger(__name__)


class AgentConfig:
    """Simple configuration for the agent system."""
    
    def __init__(self):
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
        self.GITHUB_REPO_OWNER = os.getenv("GITHUB_REPO_OWNER")
        self.GITHUB_REPO_NAME = os.getenv("GITHUB_REPO_NAME", "bitcoin-predictor")
        self.COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY")
    
    def setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=getattr(logging, self.LOG_LEVEL.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('agent.log')
            ]
        )
    
    def validate(self):
        """Validate required configuration."""
        if not self.OPENAI_API_KEY:
            return False
        return True


config = AgentConfig()


def setup_environment():
    """Setup environment and validate configuration."""
    # Setup logging
    config.setup_logging()
    
    # Validate configuration
    if not config.validate():
        logger.error("Configuration validation failed. Please check your environment variables.")
        logger.error("Required variables: OPENAI_API_KEY")
        return False
    
    logger.info("Environment setup completed successfully")
    return True


def cmd_predict(args):
    """Make a single Bitcoin price prediction."""
    print("🤖 Autonomous Agent - Bitcoin Prediction")
    print("=" * 45)
    
    try:
        agent = AutonomousAgent()
        result = agent.make_prediction(args.data_source)
        
        print(result["response"])
        return result["success"]
        
    except Exception as e:
        print(f"❌ Prediction failed: {e}")
        return False


def cmd_evaluate(args):
    """Evaluate pending predictions."""
    print("🤖 Autonomous Agent - Prediction Evaluation")
    print("=" * 50)
    
    try:
        agent = AutonomousAgent()
        result = agent.evaluate_predictions(args.min_age_hours)
        
        print(result["response"])
        return result["success"]
        
    except Exception as e:
        print(f"❌ Evaluation failed: {e}")
        return False


def cmd_test(args):
    """Test all agent components."""
    print("🧪 Testing Autonomous Agent Components")
    print("=" * 45)
    
    success = True
    
    # Test 1: Agent initialization
    print("1. Testing agent initialization...")
    try:
        agent = AutonomousAgent()
        print("   ✅ Agent initialized successfully")
    except Exception as e:
        print(f"   ❌ Agent initialization failed: {e}")
        success = False
    
    print()
    
    # Test 2: Prediction interface
    print("2. Testing prediction interface...")
    try:
        result = agent.make_prediction()
        if result["success"]:
            print("   ✅ Prediction interface working")
        else:
            print(f"   ❌ Prediction failed: {result['error']}")
            success = False
    except Exception as e:
        print(f"   ❌ Prediction interface failed: {e}")
        success = False
    
    print("\n" + "=" * 45)
    if success:
        print("✅ All tests passed! Agent is ready for operation.")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    
    return success


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Autonomous Bitcoin Prediction Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python agent_main.py predict              # Make a prediction
  python agent_main.py evaluate             # Evaluate predictions
  python agent_main.py test                 # Test all components
        """
    )
    
    # Global options
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default=config.LOG_LEVEL,
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
    
    # Evaluate command
    evaluate_parser = subparsers.add_parser('evaluate', help='Evaluate pending predictions')
    evaluate_parser.add_argument(
        '--min-age-hours',
        type=int,
        default=0,  # For testing, allow immediate evaluation
        help='Minimum age in hours before evaluation'
    )
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test all agent components')
    
    args = parser.parse_args()
    
    # Override log level if specified
    if args.log_level != config.LOG_LEVEL:
        config.LOG_LEVEL = args.log_level
    
    # Setup environment
    if not setup_environment():
        sys.exit(1)
    
    # Log startup
    logger.info(f"Starting Autonomous Agent in {args.command} mode")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    
    # Check if command was provided
    if not args.command:
        parser.print_help()
        return 1
    
    # Execute command
    command_map = {
        'predict': cmd_predict,
        'evaluate': cmd_evaluate,
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
        logger.error(f"Unexpected error in {args.command}: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 