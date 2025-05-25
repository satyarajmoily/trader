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
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add the parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from .orchestrator import AutonomousAgent
from .chains.code_analyzer import CodeAnalyzerChain
from .chains.code_improver import CodeImproverChain
from .tools.bitcoin_api import BitcoinPriceTool
from .tools.code_validator import CodeValidator
from .tools.core_system_manager import CoreSystemManager
from .interfaces.predictor_interface import PredictorInterface
from .tools.deployment_manager import DeploymentMode
import bitcoin_predictor.config as config

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
    timeframe = getattr(args, 'timeframe', '1d')
    print(f"🤖 Autonomous Agent - Bitcoin Prediction ({timeframe})")
    print("=" * 45)
    
    try:
        agent = AutonomousAgent()
        result = agent.make_prediction(args.data_source, timeframe=timeframe)
        
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
            print(f"Analyzing last {args.max_predictions} failed predictions...")
            analyses = analyzer.analyze_recent_failures(args.max_predictions)
            
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
    """Generate improved prediction code from failed predictions."""
    print("🚀 Autonomous Agent - Code Improvement")
    print("=" * 45)
    
    try:
        from .chains.code_improver import CodeImproverChain
        from .chains.code_analyzer import CodeAnalyzerChain
        
        improver = CodeImproverChain()
        
        if args.analysis_id:
            # Improve based on specific analysis
            analyzer = CodeAnalyzerChain()
            analyses = analyzer.get_analysis_history()
            
            analysis = None
            for a in analyses:
                if a.get('prediction_id') == args.analysis_id:
                    # Convert dict to AnalysisResult object
                    from .chains.code_analyzer import AnalysisResult
                    analysis = AnalysisResult(
                        prediction_id=a['prediction_id'],
                        failure_reason=a['failure_reason'],
                        market_context=a['market_context'],
                        improvement_opportunities=a['improvement_opportunities'],
                        technical_indicators_analysis=a['technical_indicators_analysis'],
                        suggested_modifications=a['suggested_modifications'],
                        confidence_score=a['confidence_score'],
                        timestamp=a['timestamp']
                    )
                    break
            
            if not analysis:
                print(f"❌ Analysis {args.analysis_id} not found")
                return False
            
            print(f"Generating improvement based on analysis {args.analysis_id}...")
            
            # Use retry logic if requested
            if args.retry:
                print(f"🔄 Using self-correcting retry logic (max {args.max_retries} retries)")
                result = improver.generate_improved_code_with_retry(
                    analysis, 
                    improvement_focus=args.focus,
                    max_retries=args.max_retries
                )
            else:
                result = improver.generate_improved_code(analysis, args.focus)
        else:
            # Generate improvements from recent failed predictions
            print("Analyzing recent failed predictions for improvements...")
            
            analyzer = CodeAnalyzerChain()
            predictor_interface = PredictorInterface()
            
            # Get recent failed predictions
            failed_predictions = predictor_interface.get_failed_predictions(limit=5)
            
            if not failed_predictions:
                print("❌ No failed predictions found to improve from")
                return False
            
            print(f"Found {len(failed_predictions)} failed predictions")
            
            # Analyze predictions first
            analysis_results = []
            for pred in failed_predictions:
                analysis = analyzer.analyze_failed_prediction(pred)
                if analysis:
                    analysis_results.append(analysis)
            
            if not analysis_results:
                print("❌ Failed to analyze predictions")
                return False
            
            # Generate improvements from analyses
            print(f"Generating improvements from {len(analysis_results)} analyses...")
            
            if args.retry:
                print(f"🔄 Using self-correcting retry logic (max {args.max_retries} retries)")
                # Use retry for the most recent analysis
                latest_analysis = analysis_results[0]
                result = improver.generate_improved_code_with_retry(
                    latest_analysis,
                    improvement_focus=args.focus,
                    max_retries=args.max_retries
                )
                results = [result] if result else []
            else:
                results = improver.generate_improvements_from_analyses(analysis_results)
        
        # Process results
        if args.retry:
            # Single result from retry logic
            if result:
                print(f"\n✅ IMPROVEMENT GENERATED:")
                print(f"ID: {result.improvement_id}")
                print(f"Validation: {'✅ PASSED' if result.validation_status == 'passed' else '❌ FAILED'}")
                print(f"Description: {result.improvement_description}")
                print(f"Confidence: {result.confidence_score:.2f}")
                print(f"Changes: {len(result.changes_made)} modifications")
                print(f"Benefits: {len(result.expected_benefits)} expected improvements")
                
                if args.show_code:
                    print(f"\n📝 IMPROVED CODE:")
                    print("=" * 40)
                    print(result.improved_code)
                    print("=" * 40)
                
                # Phase 5: Show enhanced self-correction metrics
                metrics = improver.get_self_correction_metrics()
                print(f"\n📊 ENHANCED SELF-CORRECTION METRICS:")
                print(f"   Session Success Rate: {metrics['success_rate']:.1%}")
                print(f"   Performance Status: {metrics['performance_status']}")
                print(f"   Pattern-Guided Improvements: {metrics['current_session']['pattern_guided_improvements']}")
                
                return True
            else:
                print("❌ Failed to generate valid improvement after all retries")
                
                # Phase 5: Show metrics even on failure for learning
                metrics = improver.get_self_correction_metrics()
                print(f"\n📊 SELF-CORRECTION ANALYSIS:")
                print(f"   Session Success Rate: {metrics['success_rate']:.1%}")
                print(f"   Total Attempts: {metrics['current_session']['total_attempts']}")
                print(f"   Pattern Analysis Available: {not metrics['pattern_analysis']['improvement_needed']}")
                
                return False
        else:
            # Multiple results from batch processing
            if results:
                print(f"\n✅ IMPROVEMENTS GENERATED: {len(results)}")
                for i, result in enumerate(results, 1):
                    print(f"\n{i}. {result.improvement_id}")
                    print(f"   Description: {result.improvement_description}")
                    print(f"   Confidence: {result.confidence_score:.2f}")
                    print(f"   Changes: {len(result.changes_made)} modifications")
                
                if args.show_code and results:
                    print(f"\n📝 LATEST IMPROVED CODE:")
                    print("=" * 40)
                    print(results[0].improved_code)
                    print("=" * 40)
                
                return True
            else:
                print("❌ No improvements generated")
                return False
                
    except Exception as e:
        print(f"❌ Code improvement failed: {e}")
        logger.error(f"Code improvement error: {e}")
        return False


def cmd_improve_with_retry(args):
    """Generate improved prediction code with automatic retry on validation failures."""
    print("🔄 Autonomous Agent - Self-Correcting Code Improvement")
    print("=" * 55)
    
    # Set retry parameters
    args.retry = True
    if not hasattr(args, 'max_retries'):
        args.max_retries = 3
    
    print(f"🤖 Using AI self-correction with up to {args.max_retries} retry attempts")
    print("The agent will automatically fix validation errors and retry until successful\n")
    
    return cmd_improve(args)


def cmd_pattern_analysis(args):
    """Analyze self-correction patterns for optimization insights."""
    print("📊 Enhanced Self-Correction Pattern Analysis")
    print("=" * 45)
    
    try:
        from .chains.pattern_analyzer import PatternAnalyzer
        
        analyzer = PatternAnalyzer()
        
        # Perform comprehensive pattern analysis
        print("🔍 Analyzing self-correction patterns...")
        analysis = analyzer.analyze_improvement_history()
        
        if "error" in analysis:
            print(f"❌ Analysis failed: {analysis['error']}")
            return False
        
        # Display pattern analysis results
        print(f"\n📈 PATTERN ANALYSIS RESULTS:")
        print(f"Total Attempts Analyzed: {analysis.get('total_attempts', 0)}")
        
        # Error patterns
        error_patterns = analysis.get('error_patterns', {})
        print(f"\n🚨 ERROR PATTERNS:")
        common_errors = error_patterns.get('most_common_errors', {})
        if common_errors:
            for error_type, count in list(common_errors.items())[:5]:
                likelihood = analyzer.get_error_likelihood(error_type)
                print(f"   • {error_type}: {count} occurrences ({likelihood:.1%} likelihood)")
        else:
            print("   • No significant error patterns detected")
        
        # Success patterns
        success_patterns = analysis.get('success_patterns', {})
        print(f"\n✅ SUCCESS PATTERNS:")
        print(f"   Overall Success Rate: {success_patterns.get('success_rate', 0):.1%}")
        print(f"   Successful Attempts: {success_patterns.get('total_successful', 0)}")
        
        effective_strategies = success_patterns.get('most_effective_strategies', {})
        if effective_strategies:
            print(f"   Most Effective Strategies:")
            for strategy, count in list(effective_strategies.items())[:3]:
                print(f"     • {strategy} ({count} successes)")
        
        # Retry effectiveness
        retry_patterns = analysis.get('retry_effectiveness', {})
        print(f"\n🔄 RETRY EFFECTIVENESS:")
        print(f"   Improvements with Retries: {retry_patterns.get('improvements_with_retries', 0)}")
        print(f"   Average Retries to Success: {retry_patterns.get('average_retries_to_success', 0):.1f}")
        print(f"   Retry Success Rate: {retry_patterns.get('retry_success_rate', 0):.1%}")
        
        # Recommendations
        recommendations = analysis.get('recommendations', [])
        if recommendations:
            print(f"\n💡 OPTIMIZATION RECOMMENDATIONS:")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")
        
        # Export option
        if args.export:
            filename = analyzer.export_pattern_analysis()
            print(f"\n📋 Pattern analysis exported to: {filename}")
        
        return True
        
    except Exception as e:
        print(f"❌ Pattern analysis failed: {e}")
        logger.error(f"Pattern analysis error: {e}")
        return False


def cmd_self_correction_metrics(args):
    """Display comprehensive self-correction metrics and health."""
    print("📊 Self-Correction System Health & Metrics")
    print("=" * 45)
    
    try:
        from .chains.code_improver import CodeImproverChain
        from .chains.pattern_analyzer import PatternAnalyzer
        
        # Initialize components
        improver = CodeImproverChain()
        analyzer = PatternAnalyzer()
        
        # Get current session metrics
        metrics = improver.get_self_correction_metrics()
        
        print(f"🎯 CURRENT SESSION METRICS:")
        print(f"   Total Attempts: {metrics['current_session']['total_attempts']}")
        print(f"   Successful Corrections: {metrics['current_session']['successful_corrections']}")
        print(f"   Pattern-Guided Improvements: {metrics['current_session']['pattern_guided_improvements']}")
        print(f"   Success Rate: {metrics['success_rate']:.1%}")
        print(f"   Performance Status: {metrics['performance_status']}")
        
        # Get historical patterns
        pattern_metrics = analyzer.get_success_rate_metrics()
        
        print(f"\n📈 HISTORICAL PERFORMANCE:")
        print(f"   Overall Success Rate: {pattern_metrics['overall_success_rate']:.1%}")
        print(f"   Retry Success Rate: {pattern_metrics['retry_success_rate']:.1%}")
        print(f"   Improvement Needed: {'Yes' if pattern_metrics['improvement_needed'] else 'No'}")
        
        # Performance assessment
        overall_rate = pattern_metrics['overall_success_rate']
        if overall_rate >= 0.8:
            status = "🟢 EXCELLENT"
            recommendation = "System performing optimally"
        elif overall_rate >= 0.6:
            status = "🟡 GOOD" 
            recommendation = "Minor optimizations possible"
        elif overall_rate >= 0.4:
            status = "🟠 NEEDS IMPROVEMENT"
            recommendation = "Pattern analysis recommended for optimization"
        else:
            status = "🔴 CRITICAL"
            recommendation = "Immediate pattern analysis and strategy adjustment needed"
        
        print(f"\n🎯 SYSTEM STATUS: {status}")
        print(f"   Recommendation: {recommendation}")
        
        # Error pattern summary
        if analyzer.error_patterns:
            print(f"\n🚨 TOP ERROR PATTERNS:")
            sorted_errors = sorted(analyzer.error_patterns.items(), key=lambda x: x[1], reverse=True)
            for error_type, count in sorted_errors[:3]:
                likelihood = analyzer.get_error_likelihood(error_type)
                print(f"   • {error_type}: {count} occurrences ({likelihood:.1%})")
        
        return True
        
    except Exception as e:
        print(f"❌ Metrics retrieval failed: {e}")
        logger.error(f"Self-correction metrics error: {e}")
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
    """Test all agent components including Phase 4."""
    print("🧪 Testing Autonomous Agent Components (Phase 4)")
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
        agent = AutonomousAgent()
        result = agent.make_prediction()
        if result["success"]:
            print("   ✅ Prediction interface working")
        else:
            print(f"   ❌ Prediction interface failed: {result['error']}")
            success = False
    except Exception as e:
        print(f"   ❌ Prediction interface failed: {e}")
        success = False
    
    print()
    
    # Test 3: Phase 3 - Code analyzer
    print("3. Testing code analyzer...")
    try:
        from .chains.code_analyzer import CodeAnalyzerChain
        import os
        
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            analyzer = CodeAnalyzerChain()
            print("   ✅ Code analyzer initialized")
        else:
            print("   ⚠️ Code analyzer skipped (OPENAI_API_KEY not found)")
    except Exception as e:
        print(f"   ❌ Code analyzer failed: {e}")
        success = False
    
    print()
    
    # Test 4: Phase 3 - Code improver
    print("4. Testing code improver...")
    try:
        from .chains.code_improver import CodeImproverChain
        import os
        
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            improver = CodeImproverChain()
            print("   ✅ Code improver initialized")
        else:
            print("   ⚠️ Code improver skipped (OPENAI_API_KEY not found)")
    except Exception as e:
        print(f"   ❌ Code improver failed: {e}")
        success = False
    
    print()
    
    # Test 5: Phase 3 - Code validator
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
    
    # Test 6: Phase 3 - Core system manager
    print("6. Testing core system manager...")
    try:
        core_manager = CoreSystemManager()
        backups = core_manager.get_backup_list()
        print(f"   ✅ Core system manager working ({len(backups)} backups available)")
    except Exception as e:
        print(f"   ❌ Core system manager failed: {e}")
        success = False
    
    print()
    
    # Test 7: Phase 4 - GitHub manager
    print("7. Testing GitHub manager...")
    try:
        import os
        
        github_token = os.getenv('GITHUB_TOKEN')
        if github_token:
            from .tools.github_manager import GitHubManager
            github_manager = GitHubManager()
            print("   ✅ GitHub manager initialized")
        else:
            print("   ⚠️ GitHub manager skipped (GITHUB_TOKEN not found)")
    except Exception as e:
        print(f"   ❌ GitHub manager failed: {e}")
        success = False
    
    print()
    
    # Test 8: Phase 4 - PR generator
    print("8. Testing PR generator...")
    try:
        import os
        
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            from .chains.pr_generator import PRGenerator
            pr_generator = PRGenerator(api_key)
            print("   ✅ PR generator initialized")
        else:
            print("   ⚠️ PR generator skipped (OPENAI_API_KEY not found)")
    except Exception as e:
        print(f"   ❌ PR generator failed: {e}")
        success = False
    
    print()
    
    # Test 9: Phase 4 - End-to-end GitHub integration
    print("9. Testing GitHub integration...")
    try:
        import os
        
        github_token = os.getenv('GITHUB_TOKEN')
        github_owner = os.getenv('GITHUB_REPO_OWNER')
        github_repo = os.getenv('GITHUB_REPO_NAME')
        
        if all([github_token, github_owner, github_repo]):
            agent = AutonomousAgent()
            result = agent.setup_github_integration()
            
            if result["success"]:
                print("   ✅ GitHub integration working")
                print(f"   📋 Repository: {result['repo_info']['full_name']}")
                print(f"   👤 Permissions: Push={result['repo_info']['permissions']['push']}")
            else:
                print(f"   ❌ GitHub integration failed: {result['error']}")
                success = False
        else:
            missing = []
            if not github_token: missing.append('GITHUB_TOKEN')
            if not github_owner: missing.append('GITHUB_REPO_OWNER')
            if not github_repo: missing.append('GITHUB_REPO_NAME')
            print(f"   ⚠️ GitHub integration skipped (missing: {', '.join(missing)})")
    except Exception as e:
        print(f"   ❌ GitHub integration test failed: {e}")
        success = False
    
    print("\n" + "=" * 55)
    if success:
        print("✅ All Phase 4 tests passed! Agent is ready for GitHub automation.")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        print("\n💡 Note: Some features require environment variables:")
        print("   - OPENAI_API_KEY (for Phase 3 & 4 features)")
        print("   - GITHUB_TOKEN (for Phase 4 GitHub integration)")
        print("   - GITHUB_REPO_OWNER, GITHUB_REPO_NAME (for GitHub operations)")
    
    return success


# ===== PHASE 4: GITHUB AUTOMATION COMMANDS =====

def cmd_setup_github(args):
    """Setup and test GitHub integration."""
    print("🐙 GitHub Integration Setup")
    print("=" * 30)
    
    try:
        agent = AutonomousAgent()
        result = agent.setup_github_integration()
        
        print(result["response"])
        return result["success"]
        
    except Exception as e:
        print(f"❌ GitHub setup failed: {e}")
        return False


def cmd_create_pr(args):
    """Create GitHub PR for a validated improvement."""
    print("📋 Creating GitHub PR for Improvement")
    print("=" * 40)
    
    try:
        agent = AutonomousAgent()
        result = agent.create_pr_for_improvement(args.improvement_id)
        
        print(result["response"])
        return result["success"]
        
    except Exception as e:
        print(f"❌ PR creation failed: {e}")
        return False


def cmd_list_prs(args):
    """List open autonomous improvement PRs."""
    print("📋 Autonomous Improvement PRs")
    print("=" * 30)
    
    try:
        agent = AutonomousAgent()
        result = agent.list_github_prs(args.label)
        
        print(result["response"])
        return result["success"]
        
    except Exception as e:
        print(f"❌ PR listing failed: {e}")
        return False


def cmd_check_pr(args):
    """Check status of a specific PR."""
    print(f"🔍 Checking PR #{args.pr_number}")
    print("=" * 30)
    
    try:
        agent = AutonomousAgent()
        result = agent.check_pr_status(args.pr_number)
        
        print(result["response"])
        return result["success"]
        
    except Exception as e:
        print(f"❌ PR status check failed: {e}")
        return False


def cmd_auto_cycle(args):
    """Run complete autonomous improvement cycle."""
    print("🤖 Autonomous Improvement Cycle")
    print("=" * 35)
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be made")
        print()
    
    try:
        agent = AutonomousAgent()
        
        if args.dry_run:
            # For dry run, just do analysis
            print("Step 1: Evaluating predictions...")
            eval_result = agent.evaluate_predictions()
            print(eval_result["response"])
            
            if eval_result["success"] and eval_result.get("evaluations"):
                failed_predictions = [e for e in eval_result["evaluations"] if not e.is_correct]
                
                if failed_predictions:
                    print(f"\n🔍 Would analyze {len(failed_predictions)} failed predictions")
                    print("🛠️ Would generate code improvements")
                    print("✅ Would validate improvements")
                    print("🚀 Would deploy locally")
                    
                    if not args.no_pr:
                        print("📋 Would create GitHub PR")
                    
                    print("\n💡 Use without --dry-run to execute the cycle")
                else:
                    print("\nℹ️ No failed predictions to improve from")
            
            return True
        else:
            # Run actual cycle
            create_pr = not args.no_pr
            result = agent.run_autonomous_cycle(create_pr=create_pr)
            
            print(result["response"])
            return result["success"]
        
    except Exception as e:
        print(f"❌ Autonomous cycle failed: {e}")
        return False


def cmd_autonomous(args):
    """Run autonomous operation in different deployment modes."""
    try:
        # Import deployment mode first
        from .tools.deployment_manager import DeploymentMode
        
        mode_map = {
            'production': DeploymentMode.PRODUCTION,
            'staging': DeploymentMode.STAGING, 
            'local': DeploymentMode.LOCAL,
            'demo': DeploymentMode.DEMO
        }
        
        mode = mode_map.get(args.mode, DeploymentMode.LOCAL)
        timeframe = getattr(args, 'timeframe', '1d')
        
        print(f"🤖 Autonomous Agent - {mode.value.title()} Mode ({timeframe})")
        print("=" * 55)
        
        agent = AutonomousAgent(deployment_mode=mode)
        
        if args.continuous:
            # Continuous operation mode
            result = agent.start_continuous_autonomous_operation(
                timeframe=timeframe,
                prediction_interval_minutes=getattr(args, 'prediction_interval', 1),
                evaluation_interval_minutes=getattr(args, 'evaluation_interval', 2),
                auto_restart=getattr(args, 'auto_restart', True),
                max_cycles=getattr(args, 'max_cycles', None)
            )
        else:
            # Single cycle mode
            result = agent.run_enhanced_autonomous_cycle(
                auto_restart=getattr(args, 'auto_restart', True),
                min_age_hours=getattr(args, 'min_age_hours', 0)  # Faster for demo
            )
        
        print(result["response"])
        return result["success"]
        
    except Exception as e:
        print(f"❌ Autonomous operation failed: {e}")
        return False


def cmd_demo(args):
    """Run fast demonstration of the autonomous improvement cycle."""
    print("🎬 Autonomous Agent - Fast Demo Mode")
    print("=" * 40)
    print("Demonstrating complete predict → improve → deploy → restart cycle")
    print("Using 5-minute predictions with rapid evaluation for demonstration")
    print()
    
    try:
        from .tools.deployment_manager import DeploymentMode
        
        agent = AutonomousAgent(deployment_mode=DeploymentMode.DEMO)
        
        # Fast demo cycle with 5-minute intervals
        result = agent.start_continuous_autonomous_operation(
            timeframe="5m",
            prediction_interval_minutes=5,
            evaluation_interval_minutes=5,  # Aligned with API data granularity
            auto_restart=True,
            max_cycles=3  # Limited cycles for demo
        )
        
        print(result["response"])
        return result["success"]
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Autonomous Bitcoin Prediction Agent - Phase 5: Enhanced Deployment Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Original Phase 2 Commands
  python -m autonomous_agent.main predict              # Make a prediction
  python -m autonomous_agent.main evaluate             # Evaluate predictions
  
  # Phase 3: Code Improvement Commands
  python -m autonomous_agent.main analyze              # Analyze failed predictions
  python -m autonomous_agent.main improve              # Generate improved code
  python -m autonomous_agent.main improve-retry        # 🤖 Self-correcting code improvement
  python -m autonomous_agent.main validate             # Validate generated code
  python -m autonomous_agent.main deploy               # Deploy improved code
  
  # Phase 4: GitHub Automation Commands
  python -m autonomous_agent.main setup-github         # Setup GitHub integration
  python -m autonomous_agent.main create-pr <id>       # Create PR for improvement
  python -m autonomous_agent.main list-prs             # List autonomous PRs
  python -m autonomous_agent.main check-pr <number>    # Check PR status
  python -m autonomous_agent.main auto-cycle           # Run complete autonomous cycle
  
  # Phase 5: Enhanced Autonomous Operations 🚀
  python -m autonomous_agent.main autonomous --mode local --continuous     # Local continuous operation
  python -m autonomous_agent.main autonomous --mode production             # Production PR workflow
  python -m autonomous_agent.main demo                                     # Fast demonstration mode
  
  # Local Development & Testing
  python -m autonomous_agent.main autonomous --mode local --timeframe 5m --continuous
  python -m autonomous_agent.main autonomous --mode local --prediction-interval 5 --evaluation-interval 5
  
  # Production Deployment
  python -m autonomous_agent.main autonomous --mode production --timeframe 1h
  
  # Testing
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
    predict_parser.add_argument(
        '--timeframe',
        choices=['1m', '5m', '15m', '1h', '4h', '1d'],
        default='1d',
        help='Time interval for prediction (default: 1d)'
    )
    predict_parser.set_defaults(func=cmd_predict)
    
    # Evaluate command
    evaluate_parser = subparsers.add_parser('evaluate', help='Evaluate pending predictions')
    evaluate_parser.add_argument(
        '--min-age-hours',
        type=int,
        default=0,  # For testing, allow immediate evaluation
        help='Minimum age in hours before evaluation'
    )
    evaluate_parser.set_defaults(func=cmd_evaluate)
    
    # Analyze command (Phase 3)
    analyze_parser = subparsers.add_parser('analyze', help='Analyze failed predictions for improvements')
    analyze_parser.add_argument(
        '--max-predictions',
        type=int,
        default=5,
        help='Maximum number of recent failed predictions to analyze'
    )
    analyze_parser.add_argument(
        '--prediction-id',
        help='Specific prediction ID to analyze'
    )
    analyze_parser.add_argument(
        '--detailed',
        action='store_true',
        help='Show detailed analysis results'
    )
    analyze_parser.set_defaults(func=cmd_analyze)
    
    # Improve command (Phase 3)
    improve_parser = subparsers.add_parser('improve', help='Generate improved prediction code')
    improve_parser.add_argument(
        '--analysis-id',
        help='Specific analysis ID to improve from'
    )
    improve_parser.add_argument(
        '--retry',
        action='store_true',
        help='Use self-correcting retry logic'
    )
    improve_parser.add_argument(
        '--max-retries',
        type=int,
        default=3,
        help='Maximum number of retry attempts'
    )
    improve_parser.add_argument(
        '--focus',
        help='Improvement focus area'
    )
    improve_parser.add_argument(
        '--show-code',
        action='store_true',
        help='Show generated code'
    )
    improve_parser.set_defaults(func=cmd_improve)
    
    # Self-correcting improve command
    improve_retry_parser = subparsers.add_parser('improve-retry', help='Generate improved code with automatic validation retry')
    improve_retry_parser.add_argument(
        '--analysis-id',
        help='Specific analysis ID to improve from'
    )
    improve_retry_parser.add_argument(
        '--max-retries',
        type=int,
        default=3,
        help='Maximum number of retry attempts'
    )
    improve_retry_parser.add_argument(
        '--focus',
        help='Improvement focus area'
    )
    improve_retry_parser.add_argument(
        '--show-code',
        action='store_true',
        help='Show generated code'
    )
    improve_retry_parser.set_defaults(func=cmd_improve_with_retry)
    
    # === PHASE 5: ENHANCED SELF-CORRECTION COMMANDS ===
    
    # Pattern analysis command
    pattern_parser = subparsers.add_parser('pattern-analysis', help='Analyze self-correction patterns for optimization')
    pattern_parser.add_argument(
        '--export',
        action='store_true',
        help='Export detailed pattern analysis to file'
    )
    pattern_parser.set_defaults(func=cmd_pattern_analysis)
    
    # Self-correction metrics command
    metrics_parser = subparsers.add_parser('self-correction-metrics', help='Display self-correction system health and metrics')
    metrics_parser.set_defaults(func=cmd_self_correction_metrics)
    
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
    validate_parser.set_defaults(func=cmd_validate)
    
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
    deploy_parser.set_defaults(func=cmd_deploy)
    
    # === PHASE 4: GITHUB AUTOMATION COMMANDS ===
    
    # Setup GitHub command
    setup_github_parser = subparsers.add_parser('setup-github', help='Setup and test GitHub integration')
    setup_github_parser.set_defaults(func=cmd_setup_github)
    
    # Create PR command
    create_pr_parser = subparsers.add_parser('create-pr', help='Create GitHub PR for improvement')
    create_pr_parser.add_argument(
        'improvement_id',
        help='Improvement ID to create PR for'
    )
    create_pr_parser.set_defaults(func=cmd_create_pr)
    
    # List PRs command
    list_prs_parser = subparsers.add_parser('list-prs', help='List open autonomous improvement PRs')
    list_prs_parser.add_argument(
        '--label',
        default='autonomous-improvement',
        help='Filter PRs by label (default: autonomous-improvement)'
    )
    list_prs_parser.set_defaults(func=cmd_list_prs)
    
    # Check PR command
    check_pr_parser = subparsers.add_parser('check-pr', help='Check status of a specific PR')
    check_pr_parser.add_argument(
        'pr_number',
        type=int,
        help='PR number to check'
    )
    check_pr_parser.set_defaults(func=cmd_check_pr)
    
    # Auto cycle command
    auto_cycle_parser = subparsers.add_parser('auto-cycle', help='Run complete autonomous improvement cycle')
    auto_cycle_parser.add_argument(
        '--no-pr',
        action='store_true',
        help='Skip GitHub PR creation'
    )
    auto_cycle_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Analyze and plan but do not deploy or create PR'
    )
    auto_cycle_parser.add_argument(
        '--timeframe',
        choices=['1m', '5m', '15m', '1h', '4h', '1d'],
        default='1d',
        help='Time interval for predictions (default: 1d)'
    )
    auto_cycle_parser.set_defaults(func=cmd_auto_cycle)
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test all agent components')
    test_parser.set_defaults(func=cmd_test)
    
    # Enhanced Autonomous Operation Commands (Phase 5)
    autonomous_parser = subparsers.add_parser('autonomous', help='Run autonomous operation with deployment modes')
    autonomous_parser.add_argument(
        '--mode',
        choices=['production', 'staging', 'local', 'demo'],
        default='local',
        help='Deployment mode (default: local)'
    )
    autonomous_parser.add_argument(
        '--timeframe',
        choices=['1m', '5m', '15m', '1h', '4h', '1d'],
        default='5m',
        help='Time interval for predictions (default: 5m)'
    )
    autonomous_parser.add_argument(
        '--continuous',
        action='store_true',
        help='Run continuous operation with rapid cycles'
    )
    autonomous_parser.add_argument(
        '--prediction-interval',
        type=int,
        default=5,
        help='Minutes between predictions (continuous mode)'
    )
    autonomous_parser.add_argument(
        '--evaluation-interval',
        type=int,
        default=5,
        help='Minutes between evaluation cycles (continuous mode)'
    )
    autonomous_parser.add_argument(
        '--auto-restart',
        action='store_true',
        default=True,
        help='Auto-restart after code deployment (local mode)'
    )
    autonomous_parser.add_argument(
        '--max-cycles',
        type=int,
        help='Maximum number of improvement cycles (continuous mode)'
    )
    autonomous_parser.add_argument(
        '--min-age-hours',
        type=float,
        default=0,
        help='Minimum age in hours before evaluation (for testing)'
    )
    autonomous_parser.set_defaults(func=cmd_autonomous)
    
    # Demo command
    demo_parser = subparsers.add_parser('demo', help='Run fast demonstration of autonomous cycle')
    demo_parser.add_argument(
        '--max-cycles',
        type=int,
        default=3,
        help='Maximum demo cycles to run'
    )
    demo_parser.set_defaults(func=cmd_demo)
    
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

    # Execute command using the func attribute set by set_defaults
    try:
        if hasattr(args, 'func'):
            success = args.func(args)
        else:
            print(f"❌ Unknown command: {args.command}")
            return 1
        
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