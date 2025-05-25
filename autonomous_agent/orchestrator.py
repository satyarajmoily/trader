"""Main orchestrator for the autonomous agent system."""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.schedulers.background import BackgroundScheduler
import time

from .interfaces.predictor_interface import PredictorInterface
from .chains.evaluator import EvaluatorChain
from .tools.bitcoin_api import BitcoinPriceTool

# Phase 3 imports
from .chains.code_analyzer import CodeAnalyzerChain
from .chains.code_improver import CodeImproverChain
from .tools.code_validator import CodeValidator
from .tools.core_system_manager import CoreSystemManager

# Phase 4: GitHub integration imports
from .tools.github_manager import GitHubManager
from .chains.pr_generator import PRGenerator

# Phase 5: Enhanced deployment imports
from .tools.deployment_manager import EnhancedDeploymentManager, DeploymentMode

logger = logging.getLogger(__name__)


class AutonomousAgent:
    """
    Main orchestrator for the autonomous Bitcoin prediction agent.
    
    Phase 5: Enhanced with multiple deployment modes
    - Makes predictions via the core system
    - Evaluates predictions against real market data
    - Analyzes failed predictions for improvements (Phase 3)
    - Generates improved code using LLM (Phase 3)
    - Creates GitHub PRs for autonomous improvements (Phase 4)
    - Supports local CI/CD simulation and production deployment (Phase 5)
    """
    
    def __init__(self, 
                 predictor_interface: Optional[PredictorInterface] = None,
                 evaluator_chain: Optional[EvaluatorChain] = None,
                 bitcoin_tool: Optional[BitcoinPriceTool] = None,
                 # Phase 3 components
                 code_analyzer: Optional[CodeAnalyzerChain] = None,
                 code_improver: Optional[CodeImproverChain] = None,
                 code_validator: Optional[CodeValidator] = None,
                 core_manager: Optional[CoreSystemManager] = None,
                 # Phase 4: GitHub components
                 github_manager: Optional[GitHubManager] = None,
                 pr_generator: Optional[PRGenerator] = None,
                 # Phase 5: Enhanced deployment
                 deployment_mode: DeploymentMode = DeploymentMode.LOCAL):
        """
        Initialize the autonomous agent.
        
        Args:
            predictor_interface: Interface to core prediction system
            evaluator_chain: LangChain evaluation system
            bitcoin_tool: Bitcoin price data tool
            code_analyzer: Code analysis chain (Phase 3)
            code_improver: Code improvement chain (Phase 3)
            code_validator: Code validation tool (Phase 3)
            core_manager: Core system management (Phase 3)
            github_manager: GitHub integration manager (Phase 4)
            pr_generator: PR content generator (Phase 4)
            deployment_mode: Deployment mode for improvements (Phase 5)
        """
        # Core components
        self.predictor_interface = predictor_interface or PredictorInterface()
        self.evaluator_chain = evaluator_chain or EvaluatorChain()
        self.bitcoin_tool = bitcoin_tool or BitcoinPriceTool()
        
        # Phase 3 components
        self.code_analyzer = code_analyzer
        self.code_improver = code_improver
        self.code_validator = code_validator
        self.core_manager = core_manager
        
        # Phase 4: GitHub components
        self.github_manager = github_manager
        self.pr_generator = pr_generator
        
        # Phase 5: Enhanced deployment
        self.deployment_mode = deployment_mode
        self.deployment_manager = EnhancedDeploymentManager(deployment_mode)
        
        # Initialize Phase 3 components on first use
        self._phase3_initialized = False
        # Initialize Phase 4 components on first use
        self._phase4_initialized = False
        
        self.scheduler = None
        self.is_running = False
        
    def _ensure_phase3_components(self):
        """Initialize Phase 3 components if not already done"""
        if not self._phase3_initialized:
            try:
                import os
                api_key = os.getenv('OPENAI_API_KEY')
                
                if not api_key:
                    logger.warning("OPENAI_API_KEY not found - Phase 3 features disabled")
                    return False
                
                if not self.code_analyzer:
                    self.code_analyzer = CodeAnalyzerChain(api_key)
                if not self.code_improver:
                    self.code_improver = CodeImproverChain(api_key)
                if not self.code_validator:
                    self.code_validator = CodeValidator()
                if not self.core_manager:
                    self.core_manager = CoreSystemManager()
                
                self._phase3_initialized = True
                logger.info("Phase 3 components initialized successfully")
                return True
                
            except Exception as e:
                logger.error(f"Failed to initialize Phase 3 components: {e}")
                return False
        return True
    
    def _ensure_phase4_components(self):
        """Initialize Phase 4 GitHub components if not already done"""
        if not self._phase4_initialized:
            try:
                import os
                
                # Check for required environment variables
                github_token = os.getenv('GITHUB_TOKEN')
                openai_key = os.getenv('OPENAI_API_KEY')
                
                missing_vars = []
                if not github_token:
                    missing_vars.append('GITHUB_TOKEN')
                if not openai_key:
                    missing_vars.append('OPENAI_API_KEY')
                
                if missing_vars:
                    logger.warning(f"Missing environment variables for Phase 4: {missing_vars}")
                    return False
                
                if not self.github_manager:
                    self.github_manager = GitHubManager()
                if not self.pr_generator:
                    self.pr_generator = PRGenerator(openai_key)
                
                self._phase4_initialized = True
                logger.info("Phase 4 GitHub components initialized successfully")
                return True
                
            except Exception as e:
                logger.error(f"Failed to initialize Phase 4 components: {e}")
                return False
        return True

    def make_prediction(self, data_source: Optional[str] = None, timeframe: str = "1d") -> Dict[str, Any]:
        """
        Make a Bitcoin price prediction using the core system.
        
        Args:
            data_source: Optional data source path
            timeframe: Time interval for prediction (1m, 5m, 15m, 1h, 4h, 1d)
            
        Returns:
            Dict with prediction result and metadata
        """
        try:
            logger.info(f"Making Bitcoin price prediction ({timeframe})...")
            result = self.predictor_interface.make_prediction(data_source, timeframe=timeframe)
            
            if result["success"]:
                prediction = result["prediction"]
                logger.info(f"Prediction successful: {prediction['prediction'].upper()} "
                           f"(${prediction['latest_price']:,.2f})")
                
                return {
                    "success": True,
                    "response": f"✅ Prediction {prediction['id']}: {prediction['prediction'].upper()}\n"
                               f"💰 Bitcoin Price: ${prediction['latest_price']:,.2f}\n"
                               f"🎯 Confidence: {prediction.get('confidence', 'N/A')}\n"
                               f"⏰ Timestamp: {prediction['timestamp']}"
                }
            else:
                logger.error(f"Prediction failed: {result['error']}")
                return {
                    "success": False,
                    "error": result["error"],
                    "response": f"❌ Prediction failed: {result['error']}"
                }
                
        except Exception as e:
            logger.error(f"Unexpected error in make_prediction: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": f"❌ Unexpected error: {e}"
            }
    
    def evaluate_predictions(self, min_age_hours: int = 24) -> Dict[str, Any]:
        """
        Evaluate pending predictions against real market data.
        
        Args:
            min_age_hours: Minimum age in hours before evaluation
            
        Returns:
            Dict with evaluation results
        """
        try:
            logger.info(f"Evaluating predictions older than {min_age_hours} hours...")
            evaluations = self.evaluator_chain.evaluate_pending_predictions(min_age_hours)
            
            if evaluations:
                correct_count = sum(1 for e in evaluations if e.is_correct)
                accuracy = (correct_count / len(evaluations)) * 100
                
                response = f"✅ Evaluated {len(evaluations)} predictions\n"
                response += f"🎯 Accuracy: {correct_count}/{len(evaluations)} ({accuracy:.1f}%)\n"
                
                for eval_result in evaluations:
                    status = "✅" if eval_result.is_correct else "❌"
                    response += f"{status} {eval_result.prediction_id}: "
                    response += f"{eval_result.prediction.upper()} → {eval_result.actual_movement.upper()}\n"
                
                logger.info(f"Evaluation completed: {accuracy:.1f}% accuracy")
                return {
                    "success": True,
                    "evaluations": evaluations,
                    "accuracy": accuracy,
                    "response": response.strip()
                }
            else:
                logger.info("No predictions ready for evaluation")
                return {
                    "success": True,
                    "evaluations": [],
                    "accuracy": 0.0,
                    "response": "ℹ️ No predictions ready for evaluation"
                }
                
        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": f"❌ Evaluation failed: {e}"
            }
    
    def run_analysis_cycle(self) -> Dict[str, Any]:
        """
        Run a complete analysis cycle: evaluate pending predictions, then make new prediction.
        
        Returns:
            Dict with cycle results
        """
        try:
            logger.info("Running complete analysis cycle...")
            
            # Step 1: Evaluate pending predictions
            eval_result = self.evaluate_predictions()
            
            # Step 2: Make new prediction
            pred_result = self.make_prediction()
            
            # Combine results
            response = "🔄 Analysis Cycle Complete\n"
            response += "=" * 30 + "\n"
            response += "📊 EVALUATION RESULTS:\n"
            response += eval_result["response"] + "\n\n"
            response += "🔮 NEW PREDICTION:\n"
            response += pred_result["response"]
            
            success = eval_result["success"] and pred_result["success"]
            
            logger.info("Analysis cycle completed successfully")
            return {
                "success": success,
                "evaluation": eval_result,
                "prediction": pred_result,
                "response": response
            }
            
        except Exception as e:
            logger.error(f"Analysis cycle failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": f"❌ Analysis cycle failed: {e}"
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status and statistics."""
        try:
            # Get prediction accuracy stats
            accuracy_stats = self.predictor_interface.get_prediction_accuracy()
            
            # Get current Bitcoin price
            try:
                current_price = self.bitcoin_tool.get_current_price()
                price_info = f"${current_price['price']:,.2f} ({current_price['change_24h']:+.2f}%)"
            except Exception:
                price_info = "Unable to fetch"
            
            status = {
                "system_running": self.is_running,
                "current_bitcoin_price": price_info,
                "total_predictions": accuracy_stats.get("total_predictions", 0),
                "evaluated_predictions": accuracy_stats.get("evaluated_predictions", 0),
                "accuracy_rate": accuracy_stats.get("success_rate", 0.0),
                "timestamp": datetime.now().isoformat()
            }
            
            return {
                "success": True,
                "status": status,
                "response": f"🤖 Agent Status: {'Running' if self.is_running else 'Stopped'}\n"
                           f"💰 Bitcoin: {price_info}\n"
                           f"📊 Predictions: {status['total_predictions']} total, "
                           f"{status['evaluated_predictions']} evaluated\n"
                           f"🎯 Accuracy: {status['accuracy_rate']:.1f}%"
            }
            
        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": f"❌ Status check failed: {e}"
            }
    
    def start_scheduled_operation(self, 
                                prediction_interval_hours: int = 24,
                                evaluation_interval_hours: int = 6,
                                use_background: bool = False):
        """
        Start scheduled autonomous operation.
        
        Args:
            prediction_interval_hours: Hours between predictions
            evaluation_interval_hours: Hours between evaluation checks
            use_background: Use background scheduler (non-blocking)
        """
        try:
            if self.scheduler and self.scheduler.running:
                logger.warning("Scheduler already running")
                return
            
            # Choose scheduler type
            if use_background:
                self.scheduler = BackgroundScheduler()
            else:
                self.scheduler = BlockingScheduler()
            
            # Schedule prediction making
            self.scheduler.add_job(
                func=self._scheduled_prediction,
                trigger="interval",
                hours=prediction_interval_hours,
                id="make_prediction",
                name="Make Bitcoin Prediction"
            )
            
            # Schedule evaluation checks
            self.scheduler.add_job(
                func=self._scheduled_evaluation,
                trigger="interval",
                hours=evaluation_interval_hours,
                id="evaluate_predictions",
                name="Evaluate Predictions"
            )
            
            # Start scheduler
            self.is_running = True
            logger.info(f"Starting scheduled operation: predictions every {prediction_interval_hours}h, "
                       f"evaluations every {evaluation_interval_hours}h")
            
            self.scheduler.start()
            
        except Exception as e:
            logger.error(f"Failed to start scheduled operation: {e}")
            self.is_running = False
            raise
    
    def stop_scheduled_operation(self):
        """Stop scheduled operation."""
        try:
            if self.scheduler and self.scheduler.running:
                self.scheduler.shutdown()
                logger.info("Scheduled operation stopped")
            
            self.is_running = False
            
        except Exception as e:
            logger.error(f"Failed to stop scheduled operation: {e}")
    
    def _scheduled_prediction(self):
        """Internal method for scheduled prediction making."""
        try:
            logger.info("Executing scheduled prediction...")
            result = self.make_prediction()
            if result["success"]:
                logger.info("Scheduled prediction completed successfully")
            else:
                logger.error(f"Scheduled prediction failed: {result['error']}")
        except Exception as e:
            logger.error(f"Scheduled prediction error: {e}")
    
    def _scheduled_evaluation(self):
        """Internal method for scheduled evaluation."""
        try:
            logger.info("Executing scheduled evaluation...")
            result = self.evaluate_predictions()
            if result["success"]:
                logger.info(f"Scheduled evaluation completed: {len(result['evaluations'])} predictions evaluated")
            else:
                logger.error(f"Scheduled evaluation failed: {result['error']}")
        except Exception as e:
            logger.error(f"Scheduled evaluation error: {e}")

    # ===== PHASE 4: GITHUB AUTOMATION METHODS =====
    
    def create_pr_for_improvement(self, improvement_id: str) -> Dict[str, Any]:
        """
        Create a GitHub PR for a validated code improvement.
        
        Args:
            improvement_id: ID of the improvement to create PR for
            
        Returns:
            Dict with PR creation results
        """
        try:
            if not self._ensure_phase3_components():
                return {
                    "success": False,
                    "error": "Phase 3 components not available",
                    "response": "❌ Code improvement components not configured"
                }
            
            if not self._ensure_phase4_components():
                return {
                    "success": False,
                    "error": "Phase 4 components not available",
                    "response": "❌ GitHub integration not configured"
                }
            
            logger.info(f"Creating GitHub PR for improvement {improvement_id}...")
            
            # Load improvement data from code improver
            improvements = self.code_improver.get_improvement_history()
            improvement_data = None
            for imp in improvements:
                if imp.get('improvement_id') == improvement_id:
                    improvement_data = imp
                    break
            
            if not improvement_data:
                return {
                    "success": False,
                    "error": f"Improvement {improvement_id} not found",
                    "response": f"❌ Improvement {improvement_id} not found"
                }
            
            # Load analysis and validation data
            analysis_data = improvement_data.get('analysis', {})
            validation_results = improvement_data.get('validation', {})
            
            # Step 1: Create improvement branch
            branch_name = self.github_manager.create_improvement_branch(improvement_id)
            
            # Step 2: Generate PR content
            pr_title = self.pr_generator.generate_pr_title(improvement_data)
            pr_description = self.pr_generator.generate_pr_description(
                improvement_data, analysis_data, validation_results
            )
            commit_message = self.pr_generator.generate_commit_message(improvement_data)
            
            # Step 3: Update files in branch
            code_changes = improvement_data.get('code_changes', {})
            for file_path, new_content in code_changes.items():
                self.github_manager.update_file_in_branch(
                    branch_name=branch_name,
                    file_path=file_path,
                    new_content=new_content,
                    commit_message=commit_message
                )
            
            # Step 4: Create pull request
            pr = self.github_manager.create_pull_request(
                branch_name=branch_name,
                title=pr_title,
                description=pr_description,
                labels=["autonomous-improvement", "ai-generated", "needs-review"]
            )
            
            # Step 5: Log PR creation
            pr_info = {
                "improvement_id": improvement_id,
                "pr_number": pr.number,
                "pr_url": pr.html_url,
                "branch_name": branch_name,
                "title": pr_title,
                "created_at": datetime.now().isoformat()
            }
            
            self._log_pr_creation(pr_info)
            
            logger.info(f"GitHub PR created successfully: #{pr.number}")
            return {
                "success": True,
                "pr_info": pr_info,
                "response": f"✅ GitHub PR created successfully!\n"
                           f"🔗 PR #{pr.number}: {pr_title}\n"
                           f"📋 URL: {pr.html_url}\n"
                           f"🌿 Branch: {branch_name}"
            }
            
        except Exception as e:
            logger.error(f"Failed to create PR for improvement {improvement_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": f"❌ Failed to create PR: {e}"
            }
    
    def list_github_prs(self, filter_label: Optional[str] = "autonomous-improvement") -> Dict[str, Any]:
        """
        List GitHub PRs created by the autonomous agent.
        
        Args:
            filter_label: Optional label to filter PRs
            
        Returns:
            Dict with PR list results
        """
        try:
            if not self._ensure_phase4_components():
                return {
                    "success": False,
                    "error": "Phase 4 components not available",
                    "response": "❌ GitHub integration not configured"
                }
            
            logger.info("Listing GitHub PRs...")
            prs = self.github_manager.list_open_prs(label_filter=filter_label)
            
            if not prs:
                return {
                    "success": True,
                    "prs": [],
                    "response": "ℹ️ No open autonomous improvement PRs found"
                }
            
            response = f"📋 Open Autonomous Improvement PRs ({len(prs)}):\n"
            response += "=" * 40 + "\n"
            
            for pr in prs:
                response += f"#{pr['number']}: {pr['title']}\n"
                response += f"🌿 Branch: {pr['head_branch']}\n"
                response += f"📅 Created: {pr['created_at']}\n"
                response += f"🔗 URL: {pr['url']}\n\n"
            
            return {
                "success": True,
                "prs": prs,
                "response": response.strip()
            }
            
        except Exception as e:
            logger.error(f"Failed to list GitHub PRs: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": f"❌ Failed to list PRs: {e}"
            }
    
    def check_pr_status(self, pr_number: int) -> Dict[str, Any]:
        """
        Check the status of a specific PR.
        
        Args:
            pr_number: PR number to check
            
        Returns:
            Dict with PR status information
        """
        try:
            if not self._ensure_phase4_components():
                return {
                    "success": False,
                    "error": "Phase 4 components not available",
                    "response": "❌ GitHub integration not configured"
                }
            
            logger.info(f"Checking status of PR #{pr_number}...")
            status = self.github_manager.get_pull_request_status(pr_number)
            
            response = f"📋 PR #{pr_number} Status:\n"
            response += "=" * 30 + "\n"
            response += f"📝 Title: {status['title']}\n"
            response += f"🔄 State: {status['state']}\n"
            response += f"✅ Merged: {status['merged']}\n"
            response += f"🔀 Mergeable: {status['mergeable']}\n"
            response += f"🌿 Branch: {status['head_branch']} → {status['base_branch']}\n"
            response += f"📅 Created: {status['created_at']}\n"
            response += f"👤 Author: {status['author']}\n"
            response += f"📊 Changes: +{status['additions']} -{status['deletions']} lines in {status['changed_files']} files\n"
            
            if status['reviews']:
                response += f"\n📝 Reviews ({len(status['reviews'])}):\n"
                for review in status['reviews']:
                    response += f"  • {review['user']}: {review['state']}\n"
            
            response += f"\n🔗 URL: {status['url']}"
            
            return {
                "success": True,
                "status": status,
                "response": response
            }
            
        except Exception as e:
            logger.error(f"Failed to check PR #{pr_number} status: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": f"❌ Failed to check PR status: {e}"
            }
    
    def run_autonomous_cycle(self, create_pr: bool = True) -> Dict[str, Any]:
        """
        Run a complete autonomous improvement cycle:
        1. Evaluate predictions and identify failures
        2. Analyze failed predictions for improvements
        3. Generate improved code
        4. Validate improvements
        5. Deploy improvements locally
        6. Optionally create GitHub PR
        
        Args:
            create_pr: Whether to create GitHub PR for improvements
            
        Returns:
            Dict with cycle results
        """
        try:
            logger.info("Starting autonomous improvement cycle...")
            
            # Step 1: Evaluate predictions
            eval_result = self.evaluate_predictions()
            if not eval_result["success"]:
                return {
                    "success": False,
                    "error": "Evaluation failed",
                    "response": f"❌ Cycle failed at evaluation: {eval_result['error']}"
                }
            
            # Check if we have failed predictions to analyze
            failed_predictions = [e for e in eval_result.get("evaluations", []) if not e.is_correct]
            
            if not failed_predictions:
                return {
                    "success": True,
                    "skipped": True,
                    "response": "ℹ️ No failed predictions to analyze - cycle skipped"
                }
            
            # Ensure Phase 3 components are available
            if not self._ensure_phase3_components():
                return {
                    "success": False,
                    "error": "Phase 3 components not available",
                    "response": "❌ Code improvement features not configured"
                }
            
            # Step 2: Analyze failed predictions
            logger.info(f"Analyzing {len(failed_predictions)} failed predictions...")
            analysis_result = self.code_analyzer.analyze_failed_predictions(failed_predictions)
            
            if not analysis_result.get("should_improve", False):
                return {
                    "success": True,
                    "skipped": True,
                    "response": "ℹ️ Analysis suggests no improvements needed - cycle skipped"
                }
            
            # Step 3: Generate improved code
            logger.info("Generating code improvements...")
            improvement_result = self.code_improver.generate_improved_code(
                analysis_result, failed_predictions
            )
            
            # Step 4: Validate improvements
            logger.info("Validating generated improvements...")
            validation_result = self.code_validator.validate_code(
                improvement_result["improved_code"],
                improvement_result["target_file"]
            )
            
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": "Generated code validation failed",
                    "response": f"❌ Cycle failed: {validation_result['error']}"
                }
            
            # Step 5: Deploy improvements locally
            logger.info("Deploying improvements locally...")
            deployment_result = self.core_manager.deploy_improvement(
                improvement_result["improved_code"],
                improvement_result["target_file"],
                improvement_result
            )
            
            if not deployment_result["success"]:
                return {
                    "success": False,
                    "error": "Deployment failed",
                    "response": f"❌ Cycle failed at deployment: {deployment_result['error']}"
                }
            
            improvement_id = deployment_result["improvement_id"]
            
            # Step 6: Optionally create GitHub PR
            pr_result = None
            if create_pr and self._ensure_phase4_components():
                logger.info("Creating GitHub PR for improvement...")
                pr_result = self.create_pr_for_improvement(improvement_id)
            
            # Compile results
            response = "🤖 Autonomous Improvement Cycle Complete!\n"
            response += "=" * 45 + "\n\n"
            response += f"📊 Analyzed {len(failed_predictions)} failed predictions\n"
            response += f"🔧 Generated and validated code improvements\n"
            response += f"✅ Deployed improvement: {improvement_id}\n"
            
            if pr_result and pr_result["success"]:
                response += f"📋 Created GitHub PR: #{pr_result['pr_info']['pr_number']}\n"
                response += f"🔗 PR URL: {pr_result['pr_info']['pr_url']}\n"
            elif create_pr:
                response += "⚠️ PR creation skipped (GitHub not configured)\n"
            
            response += f"\n🎯 Next: Monitor PR review and deployment"
            
            return {
                "success": True,
                "improvement_id": improvement_id,
                "pr_result": pr_result,
                "response": response
            }
            
        except Exception as e:
            logger.error(f"Autonomous cycle failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": f"❌ Autonomous cycle failed: {e}"
            }
    
    def setup_github_integration(self) -> Dict[str, Any]:
        """
        Setup and test GitHub integration.
        
        Returns:
            Dict with setup results
        """
        try:
            logger.info("Setting up GitHub integration...")
            
            if not self._ensure_phase4_components():
                return {
                    "success": False,
                    "error": "GitHub components initialization failed",
                    "response": "❌ Failed to initialize GitHub integration"
                }
            
            # Test GitHub access
            repo_info = self.github_manager.validate_access()
            
            response = "✅ GitHub Integration Setup Complete!\n"
            response += "=" * 40 + "\n"
            response += f"📋 Repository: {repo_info['full_name']}\n"
            response += f"🔒 Private: {repo_info['private']}\n"
            response += f"🌿 Default Branch: {repo_info['default_branch']}\n"
            response += f"👤 Permissions: Admin={repo_info['permissions']['admin']}, "
            response += f"Push={repo_info['permissions']['push']}\n"
            response += f"⏱️ Rate Limit: {repo_info['rate_limit']['remaining']}/{repo_info['rate_limit']['limit']}\n"
            response += "\n🎯 Ready for autonomous PR creation!"
            
            return {
                "success": True,
                "repo_info": repo_info,
                "response": response
            }
            
        except Exception as e:
            logger.error(f"GitHub integration setup failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": f"❌ GitHub setup failed: {e}"
            }
    
    def _log_pr_creation(self, pr_info: Dict[str, Any]):
        """Log PR creation for tracking"""
        try:
            import json
            log_file = "github_prs_log.json"
            
            try:
                with open(log_file, 'r') as f:
                    prs_log = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                prs_log = []
            
            prs_log.append(pr_info)
            
            with open(log_file, 'w') as f:
                json.dump(prs_log, f, indent=2)
                
            logger.info(f"PR creation logged to {log_file}")
            
        except Exception as e:
            logger.error(f"Failed to log PR creation: {e}")

    def run_enhanced_autonomous_cycle(
        self, 
        create_pr: bool = True, 
        auto_restart: bool = True,
        min_age_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Run enhanced autonomous improvement cycle with deployment mode support.
        
        This implements the PR-first approach:
        - Production: Create PR, wait for review, deploy via CI/CD
        - Local: Create branch, commit, auto-merge, deploy, restart
        - Demo: Fast local cycle for demonstration
        
        Args:
            create_pr: Whether to create GitHub PR (production/staging modes)
            auto_restart: Whether to restart process after local deployment
            min_age_hours: Minimum age for predictions to evaluate
            
        Returns:
            Dict with cycle results
        """
        try:
            logger.info(f"Starting enhanced autonomous cycle in {self.deployment_mode.value} mode...")
            
            # Step 1: Evaluate predictions
            eval_result = self.evaluate_predictions(min_age_hours)
            if not eval_result["success"]:
                return {
                    "success": False,
                    "error": "Evaluation failed",
                    "response": f"❌ Cycle failed at evaluation: {eval_result['error']}"
                }
            
            # Check if we have failed predictions to analyze
            failed_predictions = [e for e in eval_result.get("evaluations", []) if not e.is_correct]
            
            if not failed_predictions:
                return {
                    "success": True,
                    "skipped": True,
                    "response": f"ℹ️ No failed predictions to analyze in {self.deployment_mode.value} mode - cycle skipped"
                }
            
            # Ensure Phase 3 components are available
            if not self._ensure_phase3_components():
                return {
                    "success": False,
                    "error": "Phase 3 components not available",
                    "response": "❌ Code improvement features not configured"
                }
            
            # Step 2: Analyze failed predictions
            logger.info(f"Analyzing {len(failed_predictions)} failed predictions...")
            analysis_result = self.code_analyzer.analyze_failed_predictions(failed_predictions)
            
            if not analysis_result.get("should_improve", False):
                return {
                    "success": True,
                    "skipped": True,
                    "response": "ℹ️ Analysis suggests no improvements needed - cycle skipped"
                }
            
            # Step 3: Generate improved code
            logger.info("Generating code improvements...")
            improvement_result = self.code_improver.generate_improved_code(
                analysis_result, failed_predictions
            )
            
            # Step 4: Validate improvements
            logger.info("Validating generated improvements...")
            validation_result = self.code_validator.validate_code(
                improvement_result["improved_code"],
                improvement_result["target_file"]
            )
            
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": "Generated code validation failed",
                    "response": f"❌ Cycle failed: {validation_result['error']}"
                }
            
            # Step 5: Deploy using enhanced deployment manager
            logger.info(f"Deploying improvements using {self.deployment_mode.value} mode...")
            
            # Convert improvement_result to CodeImprovementResult if needed
            from .chains.code_improver import CodeImprovementResult
            if isinstance(improvement_result, dict):
                improvement = CodeImprovementResult(**improvement_result)
            else:
                improvement = improvement_result
            
            deployment_result = self.deployment_manager.deploy_improvement(
                improvement, auto_restart=auto_restart
            )
            
            if not deployment_result.get("success", False):
                return {
                    "success": False,
                    "error": "Enhanced deployment failed",
                    "response": f"❌ Cycle failed at deployment: {deployment_result.get('error', 'Unknown error')}"
                }
            
            # Compile results based on deployment mode
            response = f"🤖 Enhanced Autonomous Cycle Complete ({self.deployment_mode.value} mode)!\n"
            response += "=" * 60 + "\n\n"
            response += f"📊 Analyzed {len(failed_predictions)} failed predictions\n"
            response += f"🔧 Generated and validated code improvements\n"
            
            if self.deployment_mode == DeploymentMode.PRODUCTION:
                response += f"📋 Created GitHub PR: #{deployment_result.get('pr_number', 'N/A')}\n"
                response += f"🔗 PR URL: {deployment_result.get('pr_url', 'N/A')}\n"
                response += f"⏳ Next: Wait for human review and CI/CD deployment\n"
                
            elif self.deployment_mode == DeploymentMode.LOCAL:
                response += f"🌿 Created git branch: {deployment_result.get('branch_name', 'N/A')}\n"
                response += f"✅ Committed improvement: {deployment_result.get('commit_hash', 'N/A')[:8]}\n"
                response += f"🔀 Auto-merged to main: {deployment_result.get('merge_success', False)}\n"
                response += f"🚀 Local deployment: {improvement.improvement_id}\n"
                
                if deployment_result.get('restart_scheduled', False):
                    response += f"🔄 System restart scheduled\n"
                    response += f"⚡ Next: System will restart with new prediction logic\n"
                else:
                    response += f"🎯 Next: Manual restart required to use new logic\n"
                    
            elif self.deployment_mode == DeploymentMode.DEMO:
                response += f"🎬 Demo deployment completed\n"
                response += f"✨ Improvement: {improvement.improvement_id}\n"
                response += f"🔄 Fast cycle demonstration complete\n"
            
            return {
                "success": True,
                "deployment_mode": self.deployment_mode.value,
                "improvement_id": improvement.improvement_id,
                "deployment_result": deployment_result,
                "failed_predictions_count": len(failed_predictions),
                "response": response
            }
            
        except Exception as e:
            logger.error(f"Enhanced autonomous cycle failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": f"❌ Enhanced autonomous cycle failed: {e}"
            }

    def start_continuous_autonomous_operation(
        self,
        timeframe: str = "1m",
        prediction_interval_minutes: int = 1,
        evaluation_interval_minutes: int = 2,
        auto_restart: bool = True,
        max_cycles: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Start continuous autonomous operation with rapid cycles.
        
        This implements the complete predict → evaluate → improve → deploy → restart cycle
        optimized for local demonstration and testing.
        
        Args:
            timeframe: Prediction timeframe (1m, 5m, etc.)
            prediction_interval_minutes: Minutes between predictions
            evaluation_interval_minutes: Minutes between evaluation checks
            auto_restart: Whether to auto-restart after deployments
            max_cycles: Maximum number of cycles (None for infinite)
            
        Returns:
            Dict with operation results
        """
        try:
            cycle_count = 0
            logger.info(f"Starting continuous autonomous operation in {self.deployment_mode.value} mode")
            logger.info(f"Timeframe: {timeframe}, Prediction: every {prediction_interval_minutes}m, "
                       f"Evaluation: every {evaluation_interval_minutes}m")
            
            print(f"\n🤖 Autonomous Agent - Continuous Operation ({self.deployment_mode.value} mode)")
            print("=" * 70)
            print(f"⏰ Making predictions every {prediction_interval_minutes} minute(s)")
            print(f"🔍 Evaluating predictions every {evaluation_interval_minutes} minute(s)")
            print(f"🎯 Timeframe: {timeframe}")
            print(f"🚀 Auto-restart: {'enabled' if auto_restart else 'disabled'}")
            print(f"🔧 Auto-improvement: enabled")
            print()
            
            last_prediction_time = 0
            last_evaluation_time = 0
            
            while max_cycles is None or cycle_count < max_cycles:
                current_time = time.time()
                
                # Check if it's time to make a prediction
                if current_time - last_prediction_time >= (prediction_interval_minutes * 60):
                    try:
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔮 Making prediction...")
                        prediction_result = self.make_prediction(timeframe=timeframe)
                        
                        if prediction_result["success"]:
                            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ {prediction_result['response']}")
                        else:
                            print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Prediction failed: {prediction_result.get('error', 'Unknown error')}")
                        
                        last_prediction_time = current_time
                        
                    except Exception as e:
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Prediction error: {e}")
                
                # Check if it's time to evaluate and potentially improve
                if current_time - last_evaluation_time >= (evaluation_interval_minutes * 60):
                    try:
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔍 Evaluating predictions...")
                        
                        # Use shorter evaluation window for rapid testing
                        min_age_minutes = max(1, evaluation_interval_minutes // 2)
                        min_age_hours = min_age_minutes / 60.0
                        
                        cycle_result = self.run_enhanced_autonomous_cycle(
                            auto_restart=auto_restart,
                            min_age_hours=min_age_hours
                        )
                        
                        if cycle_result["success"]:
                            if cycle_result.get("skipped", False):
                                print(f"[{datetime.now().strftime('%H:%M:%S')}] ℹ️ {cycle_result['response']}")
                            else:
                                print(f"[{datetime.now().strftime('%H:%M:%S')}] 🎉 Improvement cycle completed!")
                                
                                # Show deployment details
                                if self.deployment_mode == DeploymentMode.LOCAL:
                                    deployment = cycle_result.get("deployment_result", {})
                                    if deployment.get("restart_scheduled", False):
                                        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 System will restart in 3 seconds...")
                                        print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚡ New prediction logic will be active after restart")
                                        # Exit gracefully - restart manager will handle restart
                                        return {
                                            "success": True,
                                            "cycles_completed": cycle_count + 1,
                                            "restart_scheduled": True,
                                            "message": "Continuous operation completed - system restarting with improved code"
                                        }
                                
                                cycle_count += 1
                        else:
                            print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Improvement cycle failed: {cycle_result.get('error', 'Unknown error')}")
                        
                        last_evaluation_time = current_time
                        
                    except Exception as e:
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Evaluation error: {e}")
                
                # Small sleep to prevent excessive CPU usage
                time.sleep(5)
            
            return {
                "success": True,
                "cycles_completed": cycle_count,
                "message": f"Continuous operation completed after {cycle_count} improvement cycles"
            }
            
        except KeyboardInterrupt:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🛑 Continuous operation stopped by user")
            return {
                "success": True,
                "cycles_completed": cycle_count,
                "message": "Continuous operation stopped by user"
            }
        except Exception as e:
            logger.error(f"Continuous operation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "cycles_completed": cycle_count,
                "message": f"Continuous operation failed: {e}"
            } 