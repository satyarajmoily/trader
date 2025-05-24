"""Main LangChain agent orchestrator for Bitcoin prediction system."""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import BaseTool
from langchain.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from tools.coingecko_tool import fetch_current_bitcoin_price, get_coingecko_client
from chains.evaluator import BitcoinPredictionEvaluator, create_evaluator
from predictor import get_latest_prediction
from config import config

logger = logging.getLogger(__name__)


class PredictionTool(BaseTool):
    """Tool for making Bitcoin price predictions."""
    
    name: str = "make_bitcoin_prediction"
    description: str = "Make a Bitcoin price prediction using OHLCV analysis"
    
    def _run(self, save_to_log: bool = True) -> str:
        """Make a Bitcoin prediction."""
        try:
            prediction_data = get_latest_prediction(save_to_log=save_to_log)
            
            if "error" in prediction_data:
                return f"Error making prediction: {prediction_data['error']}"
            
            result = f"""Bitcoin Prediction Made:
ID: {prediction_data['id']}
Prediction: {prediction_data['prediction'].upper()}
Bitcoin Price: ${prediction_data['latest_price']:,.2f}
Timestamp: {prediction_data['timestamp']}
Analysis Period: {prediction_data['analysis_period']}
Data Points: {prediction_data['data_points']}"""
            
            logger.info(f"Made prediction {prediction_data['id']}: {prediction_data['prediction']}")
            return result
            
        except Exception as e:
            error_msg = f"Failed to make prediction: {e}"
            logger.error(error_msg)
            return error_msg


class EvaluationTool(BaseTool):
    """Tool for evaluating Bitcoin predictions."""
    
    name: str = "evaluate_predictions"
    description: str = "Evaluate Bitcoin predictions against actual market data"
    
    def __init__(self, evaluator: Optional[BitcoinPredictionEvaluator] = None):
        super().__init__()
        self.evaluator = evaluator or create_evaluator()
    
    def _run(self, min_age_hours: int = 24) -> str:
        """Evaluate predictions that are old enough."""
        try:
            evaluations = self.evaluator.evaluate_pending_predictions(min_age_hours)
            
            if not evaluations:
                return "No predictions ready for evaluation or all predictions already evaluated."
            
            results = [f"Evaluation Results ({len(evaluations)} predictions):"]
            
            for eval_result in evaluations:
                status = "✅ CORRECT" if eval_result.is_correct else "❌ INCORRECT"
                results.append(f"""
- {eval_result.prediction_id}: {status}
  Predicted: {eval_result.prediction.upper()} | Actual: {eval_result.actual_movement.upper()}
  Price Change: {eval_result.price_change_percent:+.2f}%
  Confidence: {eval_result.confidence_score:.2f}
  Reasoning: {eval_result.evaluation_reasoning[:100]}...""")
            
            # Add accuracy stats
            stats = self.evaluator.get_accuracy_stats()
            results.append(f"""
Overall Accuracy: {stats['accuracy']:.1f}% ({stats['correct']}/{stats['total']} correct)""")
            
            result = "\n".join(results)
            logger.info(f"Evaluated {len(evaluations)} predictions")
            return result
            
        except Exception as e:
            error_msg = f"Failed to evaluate predictions: {e}"
            logger.error(error_msg)
            return error_msg


class BitcoinDataTool(BaseTool):
    """Tool for fetching current Bitcoin market data."""
    
    name: str = "get_bitcoin_data"
    description: str = "Fetch current Bitcoin price and market data"
    
    def _run(self, api_key: Optional[str] = None) -> str:
        """Fetch current Bitcoin data."""
        try:
            data = fetch_current_bitcoin_price(api_key or config.COINGECKO_API_KEY)
            
            result = f"""Current Bitcoin Market Data:
Price: ${data['price']:,.2f}
24h Change: {data['change_24h']:+.2f}%
Market Cap: ${data['market_cap']:,.0f}
24h Volume: ${data['volume_24h']:,.0f}
Last Updated: {data['last_updated']}"""
            
            logger.info(f"Fetched current Bitcoin price: ${data['price']:,.2f}")
            return result
            
        except Exception as e:
            error_msg = f"Failed to fetch Bitcoin data: {e}"
            logger.error(error_msg)
            return error_msg


class BitcoinPredictionAgent:
    """Main autonomous Bitcoin prediction agent."""
    
    def __init__(self, llm: Optional[ChatOpenAI] = None):
        """
        Initialize the Bitcoin prediction agent.
        
        Args:
            llm: Optional LLM instance
        """
        self.llm = llm or ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            api_key=config.OPENAI_API_KEY
        )
        
        self.evaluator = create_evaluator(self.llm)
        self.scheduler = None
        self.tools = self._create_tools()
        self.agent_executor = self._create_agent()
        
    def _create_tools(self) -> List[BaseTool]:
        """Create tools for the agent."""
        return [
            PredictionTool(),
            EvaluationTool(self.evaluator),
            BitcoinDataTool()
        ]
    
    def _create_agent(self) -> AgentExecutor:
        """Create the LangChain agent executor."""
        
        system_prompt = """You are an autonomous Bitcoin prediction agent. Your role is to:

1. Make Bitcoin price predictions using technical analysis
2. Evaluate predictions against real market data after 24 hours
3. Track prediction accuracy and identify improvement opportunities

Available tools:
- make_bitcoin_prediction: Create Bitcoin price predictions using OHLCV analysis
- evaluate_predictions: Evaluate predictions against actual market data
- get_bitcoin_data: Fetch current Bitcoin market data

Guidelines:
- Make predictions when scheduled or requested
- Evaluate predictions after they are 24+ hours old
- Provide detailed analysis of results
- Identify patterns in correct vs incorrect predictions
- Be systematic in your approach

Always provide clear, actionable insights based on the data."""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])
        
        agent = create_openai_tools_agent(self.llm, self.tools, prompt)
        
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True
        )
    
    def make_prediction(self) -> Dict:
        """Make a single Bitcoin prediction."""
        try:
            response = self.agent_executor.invoke({
                "input": "Make a Bitcoin price prediction for the next 24 hours using current market analysis."
            })
            
            return {
                "success": True,
                "response": response["output"],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to make prediction via agent: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def evaluate_predictions(self, min_age_hours: int = 24) -> Dict:
        """Evaluate pending predictions."""
        try:
            response = self.agent_executor.invoke({
                "input": f"Evaluate all predictions that are at least {min_age_hours} hours old. Provide detailed analysis of accuracy and patterns."
            })
            
            return {
                "success": True,
                "response": response["output"],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to evaluate predictions via agent: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def run_analysis_cycle(self) -> Dict:
        """Run a complete analysis cycle: prediction + evaluation."""
        try:
            response = self.agent_executor.invoke({
                "input": """Run a complete analysis cycle:
1. First, evaluate any predictions that are 24+ hours old
2. Then make a new Bitcoin prediction
3. Provide summary of current prediction accuracy
4. Identify any patterns or insights for improvement"""
            })
            
            return {
                "success": True,
                "response": response["output"],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to run analysis cycle: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def start_scheduled_operation(self, 
                                prediction_interval_hours: int = 24,
                                evaluation_interval_hours: int = 6,
                                use_background: bool = True) -> None:
        """
        Start scheduled autonomous operation.
        
        Args:
            prediction_interval_hours: Hours between predictions
            evaluation_interval_hours: Hours between evaluation checks
            use_background: Use background scheduler (True) or blocking (False)
        """
        if use_background:
            self.scheduler = BackgroundScheduler()
        else:
            self.scheduler = BlockingScheduler()
        
        # Schedule predictions
        self.scheduler.add_job(
            self._scheduled_prediction,
            IntervalTrigger(hours=prediction_interval_hours),
            id='prediction_job',
            name='Bitcoin Prediction',
            max_instances=1
        )
        
        # Schedule evaluations
        self.scheduler.add_job(
            self._scheduled_evaluation,
            IntervalTrigger(hours=evaluation_interval_hours),
            id='evaluation_job',
            name='Prediction Evaluation',
            max_instances=1
        )
        
        # Start scheduler
        self.scheduler.start()
        logger.info(f"Started scheduled operation - Predictions: every {prediction_interval_hours}h, Evaluations: every {evaluation_interval_hours}h")
        
        if not use_background:
            try:
                # Keep the script running
                self.scheduler.start()
            except KeyboardInterrupt:
                logger.info("Stopping scheduled operation...")
                self.scheduler.shutdown()
    
    def _scheduled_prediction(self):
        """Scheduled prediction job."""
        logger.info("Running scheduled prediction...")
        result = self.make_prediction()
        
        if result["success"]:
            logger.info("Scheduled prediction completed successfully")
        else:
            logger.error(f"Scheduled prediction failed: {result['error']}")
    
    def _scheduled_evaluation(self):
        """Scheduled evaluation job."""
        logger.info("Running scheduled evaluation...")
        result = self.evaluate_predictions()
        
        if result["success"]:
            logger.info("Scheduled evaluation completed successfully")
        else:
            logger.error(f"Scheduled evaluation failed: {result['error']}")
    
    def stop_scheduled_operation(self):
        """Stop the scheduled operation."""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Stopped scheduled operation")


def create_agent(llm: Optional[ChatOpenAI] = None) -> BitcoinPredictionAgent:
    """Factory function to create Bitcoin prediction agent."""
    return BitcoinPredictionAgent(llm=llm)


if __name__ == "__main__":
    # Test the agent
    print("Testing Bitcoin Prediction Agent")
    print("=" * 40)
    
    try:
        # Validate configuration
        if not config.validate():
            print("❌ Configuration validation failed. Please check your environment variables.")
            exit(1)
        
        # Setup logging
        config.setup_logging()
        
        # Create agent
        agent = create_agent()
        
        # Test prediction
        print("Making test prediction...")
        result = agent.make_prediction()
        
        if result["success"]:
            print("✅ Prediction successful:")
            print(result["response"])
        else:
            print(f"❌ Prediction failed: {result['error']}")
        
        print("\n" + "-" * 30)
        
        # Test evaluation
        print("Testing evaluation...")
        result = agent.evaluate_predictions(min_age_hours=0)  # 0 for testing
        
        if result["success"]:
            print("✅ Evaluation successful:")
            print(result["response"])
        else:
            print(f"❌ Evaluation failed: {result['error']}")
        
        print("\n" + "=" * 40)
        print("✅ Agent test completed successfully!")
        
    except Exception as e:
        print(f"❌ Agent test failed: {e}")
        logger.exception("Agent test failed") 