"""Main entry point for the Autonomous Bitcoin Prediction Agent."""

import argparse
import logging
import sys
import time
from datetime import datetime

from chains.agent import create_agent
from config import config

logger = logging.getLogger(__name__)


def setup_environment():
    """Setup environment and validate configuration."""
    # Setup logging
    config.setup_logging()
    
    # Validate configuration
    if not config.validate():
        logger.error("Configuration validation failed. Please check your environment variables.")
        logger.error("Required variables: OPENAI_API_KEY, GITHUB_TOKEN, GITHUB_REPO_OWNER")
        return False
    
    logger.info("Environment setup completed successfully")
    return True


def run_single_prediction():
    """Run a single prediction cycle."""
    logger.info("Running single prediction...")
    
    agent = create_agent()
    result = agent.make_prediction()
    
    if result["success"]:
        print("✅ Prediction completed successfully:")
        print(result["response"])
        logger.info("Single prediction completed successfully")
    else:
        print(f"❌ Prediction failed: {result['error']}")
        logger.error(f"Single prediction failed: {result['error']}")
        return False
    
    return True


def run_single_evaluation():
    """Run a single evaluation cycle."""
    logger.info("Running single evaluation...")
    
    agent = create_agent()
    result = agent.evaluate_predictions(min_age_hours=0)  # Evaluate all for testing
    
    if result["success"]:
        print("✅ Evaluation completed successfully:")
        print(result["response"])
        logger.info("Single evaluation completed successfully")
    else:
        print(f"❌ Evaluation failed: {result['error']}")
        logger.error(f"Single evaluation failed: {result['error']}")
        return False
    
    return True


def run_analysis_cycle():
    """Run a complete analysis cycle."""
    logger.info("Running complete analysis cycle...")
    
    agent = create_agent()
    result = agent.run_analysis_cycle()
    
    if result["success"]:
        print("✅ Analysis cycle completed successfully:")
        print(result["response"])
        logger.info("Analysis cycle completed successfully")
    else:
        print(f"❌ Analysis cycle failed: {result['error']}")
        logger.error(f"Analysis cycle failed: {result['error']}")
        return False
    
    return True


def run_autonomous_mode():
    """Run the agent in autonomous mode with scheduling."""
    logger.info("Starting autonomous mode...")
    
    try:
        agent = create_agent()
        
        print("🤖 Starting Autonomous Bitcoin Prediction Agent")
        print("=" * 50)
        print(f"Prediction interval: {config.PREDICTION_INTERVAL_HOURS} hours")
        print("Press Ctrl+C to stop")
        print("=" * 50)
        
        # Start scheduled operation
        agent.start_scheduled_operation(
            prediction_interval_hours=config.PREDICTION_INTERVAL_HOURS,
            evaluation_interval_hours=6,  # Check for evaluations every 6 hours
            use_background=False  # Use blocking scheduler
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping autonomous mode...")
        logger.info("Autonomous mode stopped by user")
        
    except Exception as e:
        logger.error(f"Autonomous mode failed: {e}")
        print(f"❌ Autonomous mode failed: {e}")
        return False
    
    return True


def run_test_mode():
    """Run comprehensive tests of all components."""
    logger.info("Running test mode...")
    
    print("🧪 Testing Bitcoin Prediction Agent Components")
    print("=" * 50)
    
    success = True
    
    # Test 1: Single prediction
    print("1. Testing single prediction...")
    if not run_single_prediction():
        success = False
    
    print("\n" + "-" * 30)
    
    # Test 2: Single evaluation
    print("2. Testing single evaluation...")
    if not run_single_evaluation():
        success = False
    
    print("\n" + "-" * 30)
    
    # Test 3: Analysis cycle
    print("3. Testing analysis cycle...")
    if not run_analysis_cycle():
        success = False
    
    print("\n" + "=" * 50)
    
    if success:
        print("✅ All tests passed! Agent is ready for autonomous operation.")
        logger.info("All tests passed successfully")
    else:
        print("❌ Some tests failed. Please check the logs.")
        logger.error("Some tests failed")
    
    return success


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Autonomous Bitcoin Prediction Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py predict           # Make a single prediction
  python main.py evaluate          # Evaluate pending predictions
  python main.py cycle             # Run complete analysis cycle
  python main.py autonomous        # Start autonomous operation
  python main.py test              # Run comprehensive tests
        """
    )
    
    parser.add_argument(
        'mode',
        choices=['predict', 'evaluate', 'cycle', 'autonomous', 'test'],
        help='Operation mode'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default=config.LOG_LEVEL,
        help='Logging level'
    )
    
    args = parser.parse_args()
    
    # Override log level if specified
    if args.log_level != config.LOG_LEVEL:
        config.LOG_LEVEL = args.log_level
    
    # Setup environment
    if not setup_environment():
        sys.exit(1)
    
    # Log startup
    logger.info(f"Starting Bitcoin Prediction Agent in {args.mode} mode")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    
    # Route to appropriate function
    try:
        if args.mode == 'predict':
            success = run_single_prediction()
        elif args.mode == 'evaluate':
            success = run_single_evaluation()
        elif args.mode == 'cycle':
            success = run_analysis_cycle()
        elif args.mode == 'autonomous':
            success = run_autonomous_mode()
        elif args.mode == 'test':
            success = run_test_mode()
        else:
            logger.error(f"Unknown mode: {args.mode}")
            success = False
        
        if success:
            logger.info(f"Agent {args.mode} mode completed successfully")
            sys.exit(0)
        else:
            logger.error(f"Agent {args.mode} mode failed")
            sys.exit(1)
            
    except Exception as e:
        logger.exception(f"Unexpected error in {args.mode} mode")
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 