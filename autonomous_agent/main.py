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
from .chains.code_analyzer import CodeAnalyzerChain
from .chains.code_improver import CodeImproverChain
from .tools.code_validator import CodeValidator
from .tools.core_system_manager import CoreSystemManager

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


def cmd_analyze(args):
    """Analyze failed predictions for improvement opportunities."""
    print("🧠 Autonomous Agent - Code Analysis")
    print("=" * 40)
    
    try:
        analyzer = CodeAnalyzerChain()
        
        if args.prediction_id:
            # Analyze specific prediction
            print(f"Analyzing prediction {args.prediction_id}...")
            analysis = analyzer.analyze_failed_prediction(args.prediction_id)
            
            if analysis:
                print("✅ Analysis completed successfully")
                print(f"\n📊 ANALYSIS RESULTS:")
                print(f"Prediction ID: {analysis.prediction_id}")
                print(f"Failure Reason: {analysis.failure_reason}")
                print(f"Market Context: {analysis.market_context}")
                print(f"\n🎯 Improvement Opportunities:")
                for opp in analysis.improvement_opportunities:
                    print(f"  • {opp}")
                print(f"\n💡 Suggested Modifications:")
                for mod in analysis.suggested_modifications:
                    print(f"  • {mod}")
                print(f"\n🔍 Confidence Score: {analysis.confidence_score:.2f}")
                return True
            else:
                print("❌ Analysis failed - prediction not found or not failed")
                return False
        else:
            # Analyze recent failures
            print(f"Analyzing last {args.max_failures} failed predictions...")
            analyses = analyzer.analyze_recent_failures(args.max_failures)
            
            if analyses:
                print(f"✅ Analyzed {len(analyses)} failed predictions")
                
                # Show summary
                summary = analyzer.get_improvement_summary(analyses)
                print(f"\n📊 IMPROVEMENT SUMMARY:")
                print(f"Total Analyses: {summary['total_analyses']}")
                print(f"Average Confidence: {summary['average_confidence']:.2f}")
                
                print(f"\n🔥 Most Common Opportunities:")
                for opp, count in summary['common_opportunities'][:3]:
                    print(f"  • {opp} ({count}x)")
                
                print(f"\n💡 Most Common Modifications:")
                for mod, count in summary['common_modifications'][:3]:
                    print(f"  • {mod} ({count}x)")
                
                return True
            else:
                print("ℹ️ No recent failed predictions found to analyze")
                return True
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        logger.error(f"Analysis error: {e}")
        return False


def cmd_improve(args):
    """Generate improved prediction code based on analysis."""
    print("🛠️ Autonomous Agent - Code Improvement")
    print("=" * 45)
    
    try:
        # First analyze failures to get improvement targets
        analyzer = CodeAnalyzerChain()
        improver = CodeImproverChain()
        
        print("Step 1: Analyzing recent failures...")
        analyses = analyzer.analyze_recent_failures(args.max_failures)
        
        if not analyses:
            print("ℹ️ No recent failed predictions found to improve from")
            return True
        
        print(f"✅ Found {len(analyses)} failed predictions to improve from")
        
        print("\nStep 2: Generating improved code...")
        improvements = improver.generate_improvements_from_analyses(analyses)
        
        if improvements:
            print(f"✅ Generated {len(improvements)} code improvements")
            
            for improvement in improvements:
                print(f"\n🆔 Improvement ID: {improvement.improvement_id}")
                print(f"📝 Description: {improvement.improvement_description}")
                print(f"🔧 Changes Made:")
                for change in improvement.changes_made[:3]:  # Show first 3
                    print(f"  • {change}")
                print(f"✨ Expected Benefits:")
                for benefit in improvement.expected_benefits[:3]:  # Show first 3  
                    print(f"  • {benefit}")
                print(f"🎯 Confidence: {improvement.confidence_score:.2f}")
                
                if args.show_code:
                    print(f"\n💻 Generated Code Preview:")
                    code_lines = improvement.improved_code.split('\n')
                    for line in code_lines[:10]:  # Show first 10 lines
                        print(f"    {line}")
                    if len(code_lines) > 10:
                        print(f"    ... ({len(code_lines)-10} more lines)")
                
            return True
        else:
            print("❌ Failed to generate code improvements")
            return False
            
    except Exception as e:
        print(f"❌ Code improvement failed: {e}")
        logger.error(f"Improvement error: {e}")
        return False


def cmd_validate(args):
    """Validate generated code for safety and compatibility."""
    print("✅ Autonomous Agent - Code Validation")
    print("=" * 45)
    
    try:
        validator = CodeValidator()
        
        if args.improvement_id:
            # Load specific improvement for validation
            improver = CodeImproverChain()
            improvements = improver.get_improvement_history()
            
            improvement = None
            for imp in improvements:
                if imp.get('improvement_id') == args.improvement_id:
                    improvement = imp
                    break
            
            if not improvement:
                print(f"❌ Improvement {args.improvement_id} not found")
                return False
            
            print(f"Validating improvement {args.improvement_id}...")
            result = validator.comprehensive_validation(
                improvement['improved_code'], 
                test_execution=args.test_execution
            )
        else:
            # Validate current system
            print("Validating current core system...")
            core_manager = CoreSystemManager()
            result = core_manager.validate_current_system()
        
        print(f"\n📊 VALIDATION RESULTS:")
        print(f"Overall Valid: {'✅' if result.get('overall_valid', False) else '❌'}")
        print(f"Summary: {result.get('summary', 'No summary available')}")
        
        if args.detailed:
            interface_result = result.get('interface_compatibility', {})
            if interface_result:
                print(f"\n🔍 DETAILED RESULTS:")
                print(f"Syntax: {'✅' if interface_result.get('syntax', {}).get('valid', False) else '❌'}")
                print(f"Signature: {'✅' if interface_result.get('signature', {}).get('valid', False) else '❌'}")
                print(f"Imports: {'✅' if interface_result.get('imports', {}).get('valid', False) else '❌'}")
                print(f"Return Type: {'✅' if interface_result.get('return_type', {}).get('valid', False) else '❌'}")
            
            if args.test_execution and 'execution_test' in result:
                exec_result = result['execution_test']
                print(f"Execution Test: {'✅' if exec_result.get('valid', False) else '❌'}")
                if exec_result.get('output'):
                    print(f"Test Output: {exec_result['output']}")
        
        return result.get('overall_valid', False)
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        logger.error(f"Validation error: {e}")
        return False


def cmd_deploy(args):
    """Deploy improved code to the core system."""
    print("🚀 Autonomous Agent - Code Deployment")
    print("=" * 45)
    
    try:
        if not args.improvement_id:
            print("❌ Improvement ID required for deployment")
            return False
        
        # Load the improvement
        improver = CodeImproverChain()
        improvements = improver.get_improvement_history()
        
        improvement = None
        for imp in improvements:
            if imp.get('improvement_id') == args.improvement_id:
                # Convert dict to CodeImprovementResult for compatibility
                from .chains.code_improver import CodeImprovementResult
                improvement = CodeImprovementResult(**imp)
                break
        
        if not improvement:
            print(f"❌ Improvement {args.improvement_id} not found")
            return False
        
        print(f"Deploying improvement {args.improvement_id}...")
        
        # Deploy using core system manager
        core_manager = CoreSystemManager()
        result = core_manager.deploy_improved_code(
            improvement, 
            validate_before_deploy=not args.skip_validation
        )
        
        if result.get('success', False):
            print("✅ Deployment successful!")
            print(f"📝 Deployment ID: {result['deployment_id']}")
            print(f"💾 Backup Created: {result['backup_info']['backup_id']}")
            print(f"🎯 Changes: {len(improvement.changes_made)} modifications")
            print(f"✨ Expected Benefits: {len(improvement.expected_benefits)} improvements")
            
            if not args.skip_validation:
                validation_result = result.get('validation_result', {})
                print(f"✅ Validation: {'Passed' if validation_result.get('overall_valid', False) else 'Failed'}")
            
            return True
        else:
            print("❌ Deployment failed!")
            print(f"Error: {result.get('error', 'Unknown error')}")
            print(f"Message: {result.get('message', 'No message')}")
            return False
            
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        logger.error(f"Deployment error: {e}")
        return False


def cmd_test(args):
    """Test all agent components including Phase 3."""
    print("🧪 Testing Autonomous Agent Components (Phase 3)")
    print("=" * 55)
    
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
    
    print()
    
    # Test 3: Code analyzer
    print("3. Testing code analyzer...")
    try:
        analyzer = CodeAnalyzerChain()
        print("   ✅ Code analyzer initialized")
    except Exception as e:
        print(f"   ❌ Code analyzer failed: {e}")
        success = False
    
    print()
    
    # Test 4: Code improver
    print("4. Testing code improver...")
    try:
        improver = CodeImproverChain()
        print("   ✅ Code improver initialized")
    except Exception as e:
        print(f"   ❌ Code improver failed: {e}")
        success = False
    
    print()
    
    # Test 5: Code validator
    print("5. Testing code validator...")
    try:
        validator = CodeValidator()
        # Test with simple valid code
        test_code = """
def analyze(self, price_data):
    return AnalysisResult(
        short_ma=1.0, long_ma=1.0, momentum=0.0, volume_trend=1.0,
        bullish_signals=1.0, prediction="up", confidence=0.7, reasoning=[]
    )"""
        result = validator.validate_syntax(test_code)
        if result.get('valid', False):
            print("   ✅ Code validator working")
        else:
            print(f"   ❌ Code validator failed: {result.get('message', 'Unknown error')}")
            success = False
    except Exception as e:
        print(f"   ❌ Code validator failed: {e}")
        success = False
    
    print()
    
    # Test 6: Core system manager
    print("6. Testing core system manager...")
    try:
        core_manager = CoreSystemManager()
        backups = core_manager.get_backup_list()
        print(f"   ✅ Core system manager working ({len(backups)} backups available)")
    except Exception as e:
        print(f"   ❌ Core system manager failed: {e}")
        success = False
    
    print("\n" + "=" * 55)
    if success:
        print("✅ All Phase 3 tests passed! Agent is ready for code improvement.")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    
    return success


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Autonomous Bitcoin Prediction Agent - Phase 3",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Original Phase 2 Commands
  python -m autonomous_agent.main predict              # Make a prediction
  python -m autonomous_agent.main evaluate             # Evaluate predictions
  
  # New Phase 3 Commands
  python -m autonomous_agent.main analyze              # Analyze failed predictions
  python -m autonomous_agent.main improve              # Generate improved code
  python -m autonomous_agent.main validate             # Validate generated code
  python -m autonomous_agent.main deploy               # Deploy improved code
  python -m autonomous_agent.main test                 # Test all components
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
    
    # Analyze command (Phase 3)
    analyze_parser = subparsers.add_parser('analyze', help='Analyze failed predictions for improvements')
    analyze_parser.add_argument(
        '--prediction-id',
        help='Specific prediction ID to analyze'
    )
    analyze_parser.add_argument(
        '--max-failures',
        type=int,
        default=5,
        help='Maximum number of recent failures to analyze'
    )
    
    # Improve command (Phase 3)
    improve_parser = subparsers.add_parser('improve', help='Generate improved prediction code')
    improve_parser.add_argument(
        '--max-failures',
        type=int,
        default=3,
        help='Maximum number of recent failures to improve from'
    )
    improve_parser.add_argument(
        '--show-code',
        action='store_true',
        help='Show generated code preview'
    )
    
    # Validate command (Phase 3)
    validate_parser = subparsers.add_parser('validate', help='Validate generated code')
    validate_parser.add_argument(
        '--improvement-id',
        help='Specific improvement ID to validate'
    )
    validate_parser.add_argument(
        '--test-execution',
        action='store_true',
        default=True,
        help='Test code execution (default: True)'
    )
    validate_parser.add_argument(
        '--detailed',
        action='store_true',
        help='Show detailed validation results'
    )
    
    # Deploy command (Phase 3)
    deploy_parser = subparsers.add_parser('deploy', help='Deploy improved code to core system')
    deploy_parser.add_argument(
        'improvement_id',
        help='Improvement ID to deploy'
    )
    deploy_parser.add_argument(
        '--skip-validation',
        action='store_true',
        help='Skip validation before deployment (not recommended)'
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
        'analyze': cmd_analyze,      # Phase 3
        'improve': cmd_improve,      # Phase 3
        'validate': cmd_validate,    # Phase 3
        'deploy': cmd_deploy,        # Phase 3
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