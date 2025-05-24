"""Main orchestrator for the autonomous agent system."""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.schedulers.background import BackgroundScheduler

from .interfaces.predictor_interface import PredictorInterface
from .chains.evaluator import EvaluatorChain
from .tools.bitcoin_api import BitcoinPriceTool

logger = logging.getLogger(__name__)


class AutonomousAgent:
    """
    Main orchestrator for the autonomous Bitcoin prediction agent.
    
    This class coordinates all agent activities:
    - Making predictions via the core system
    - Evaluating predictions against real market data
    - Future: Improving prediction code when failures occur
    """
    
    def __init__(self, 
                 predictor_interface: Optional[PredictorInterface] = None,
                 evaluator_chain: Optional[EvaluatorChain] = None,
                 bitcoin_tool: Optional[BitcoinPriceTool] = None):
        """
        Initialize the autonomous agent.
        
        Args:
            predictor_interface: Interface to core prediction system
            evaluator_chain: LangChain evaluation system
            bitcoin_tool: Bitcoin price data tool
        """
        self.predictor_interface = predictor_interface or PredictorInterface()
        self.evaluator_chain = evaluator_chain or EvaluatorChain()
        self.bitcoin_tool = bitcoin_tool or BitcoinPriceTool()
        
        self.scheduler = None
        self.is_running = False
        
    def make_prediction(self, data_source: Optional[str] = None) -> Dict[str, Any]:
        """
        Make a Bitcoin price prediction using the core system.
        
        Args:
            data_source: Optional data source path
            
        Returns:
            Dict with prediction result and metadata
        """
        try:
            logger.info("Making Bitcoin price prediction...")
            result = self.predictor_interface.make_prediction(data_source)
            
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
                logger.info(f"Scheduled evaluation completed: {result.get('accuracy', 0):.1f}% accuracy")
            else:
                logger.error(f"Scheduled evaluation failed: {result['error']}")
        except Exception as e:
            logger.error(f"Scheduled evaluation error: {e}") 