"""LangChain evaluation chain for Bitcoin prediction accuracy assessment."""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Literal
from pathlib import Path

from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.schema import BaseOutputParser
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from ..tools.bitcoin_api import BitcoinPriceTool
from ..interfaces.predictor_interface import PredictorInterface

logger = logging.getLogger(__name__)

PredictionResult = Literal["up", "down"]


class EvaluationResult(BaseModel):
    """Structured evaluation result."""
    prediction_id: str
    prediction: PredictionResult  
    actual_movement: PredictionResult
    is_correct: bool
    confidence_score: float = Field(ge=0, le=1)
    price_change_percent: float
    evaluation_reasoning: str
    timestamp: str
    

class EvaluationOutputParser(BaseOutputParser[EvaluationResult]):
    """Parser for LLM evaluation output."""
    
    def parse(self, text: str) -> EvaluationResult:
        """Parse LLM output into structured evaluation result."""
        try:
            # Extract JSON from LLM response
            import re
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                result_dict = json.loads(json_match.group())
                return EvaluationResult(**result_dict)
            else:
                raise ValueError("No JSON found in LLM response")
        except Exception as e:
            logger.error(f"Failed to parse evaluation output: {e}")
            # Return default evaluation result
            return EvaluationResult(
                prediction_id="unknown",
                prediction="down",
                actual_movement="down", 
                is_correct=False,
                confidence_score=0.0,
                price_change_percent=0.0,
                evaluation_reasoning=f"Parsing failed: {e}",
                timestamp=datetime.now().isoformat()
            )


class EvaluatorChain:
    """LangChain-based evaluator for Bitcoin predictions using the agent architecture."""
    
    def __init__(self, 
                 llm: Optional[ChatOpenAI] = None,
                 predictor_interface: Optional[PredictorInterface] = None,
                 bitcoin_tool: Optional[BitcoinPriceTool] = None):
        """
        Initialize the prediction evaluator.
        
        Args:
            llm: Optional LLM instance, will create default if not provided
            predictor_interface: Interface to the core prediction system
            bitcoin_tool: Bitcoin price fetching tool
        """
        self.llm = llm or ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            max_tokens=1000
        )
        
        self.predictor_interface = predictor_interface or PredictorInterface()
        self.bitcoin_tool = bitcoin_tool or BitcoinPriceTool()
        self.evaluation_chain = self._create_evaluation_chain()
        self.evaluations_file = Path("evaluations_log.json")
        
    def _create_evaluation_chain(self) -> LLMChain:
        """Create the LangChain evaluation chain."""
        
        evaluation_prompt = PromptTemplate(
            input_variables=[
                "prediction",
                "prediction_time", 
                "prediction_price",
                "current_price",
                "price_change_percent",
                "actual_movement",
                "market_context"
            ],
            template="""You are a Bitcoin prediction accuracy evaluator. Analyze the following prediction and provide a detailed evaluation.

PREDICTION DETAILS:
- Prediction: {prediction} (UP or DOWN)
- Made at: {prediction_time}
- Bitcoin price when predicted: ${prediction_price:,.2f}
- Current Bitcoin price: ${current_price:,.2f}
- Actual price change: {price_change_percent:+.2f}%
- Actual movement: {actual_movement}

MARKET CONTEXT:
{market_context}

EVALUATION CRITERIA:
1. Compare predicted direction vs actual movement
2. Consider the magnitude of price change
3. Assess prediction quality in market context
4. Provide confidence score (0.0 to 1.0) for the evaluation

Respond with ONLY a JSON object in this exact format:
{{
    "prediction_id": "{prediction_id}",
    "prediction": "{prediction}",
    "actual_movement": "{actual_movement}",
    "is_correct": true/false,
    "confidence_score": 0.0-1.0,
    "price_change_percent": {price_change_percent},
    "evaluation_reasoning": "Detailed explanation of the evaluation",
    "timestamp": "{timestamp}"
}}

Make sure the JSON is valid and complete."""
        )
        
        return LLMChain(
            llm=self.llm,
            prompt=evaluation_prompt,
            output_parser=EvaluationOutputParser()
        )
    
    def _save_evaluation(self, evaluation: EvaluationResult):
        """Save evaluation result to JSON file."""
        evaluations = []
        
        # Load existing evaluations
        if self.evaluations_file.exists():
            try:
                with open(self.evaluations_file, 'r') as f:
                    evaluations = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load existing evaluations: {e}")
        
        # Add new evaluation
        evaluations.append(evaluation.dict())
        
        # Save back to file
        try:
            with open(self.evaluations_file, 'w') as f:
                json.dump(evaluations, f, indent=2)
            logger.info(f"Saved evaluation for prediction {evaluation.prediction_id}")
        except Exception as e:
            logger.error(f"Failed to save evaluation: {e}")
    
    def _create_market_context(self, price_change: float) -> str:
        """Create market context description."""
        abs_change = abs(price_change)
        
        if abs_change < 1:
            volatility = "low"
        elif abs_change < 5:
            volatility = "moderate"
        elif abs_change < 10:
            volatility = "high"
        else:
            volatility = "extreme"
            
        direction = "upward" if price_change > 0 else "downward"
        
        return f"Market showed {volatility} volatility with {direction} movement of {abs_change:.2f}%"
    
    def evaluate_prediction(self, prediction_id: str) -> Optional[EvaluationResult]:
        """
        Evaluate a specific prediction against actual Bitcoin price movement.
        
        Args:
            prediction_id: ID of the prediction to evaluate
            
        Returns:
            EvaluationResult if successful, None if failed
        """
        try:
            # Get prediction from storage
            prediction_record = self.predictor_interface.storage.get_prediction_by_id(prediction_id)
            if not prediction_record:
                logger.error(f"Prediction {prediction_id} not found")
                return None
            
            # Get current Bitcoin price
            current_price_data = self.bitcoin_tool.get_current_price()
            current_price = current_price_data["price"]
            
            # Calculate price change
            price_change = self.bitcoin_tool.calculate_price_change(
                prediction_record.latest_price, 
                current_price
            )
            
            # Determine actual movement
            actual_movement = price_change["direction"]
            
            # Create market context
            market_context = self._create_market_context(price_change["change_percent"])
            
            # Run LLM evaluation
            evaluation_input = {
                "prediction": prediction_record.prediction,
                "prediction_time": prediction_record.timestamp,
                "prediction_price": prediction_record.latest_price,
                "current_price": current_price,
                "price_change_percent": price_change["change_percent"],
                "actual_movement": actual_movement,
                "market_context": market_context,
                "prediction_id": prediction_id,
                "timestamp": datetime.now().isoformat()
            }
            
            evaluation = self.evaluation_chain.run(**evaluation_input)
            
            # Update prediction record with outcome
            self.predictor_interface.update_prediction_outcome(
                prediction_id=prediction_id,
                actual_outcome=actual_movement,
                actual_price=current_price
            )
            
            # Save evaluation
            self._save_evaluation(evaluation)
            
            logger.info(f"Evaluated prediction {prediction_id}: {evaluation.is_correct}")
            return evaluation
            
        except Exception as e:
            logger.error(f"Failed to evaluate prediction {prediction_id}: {e}")
            return None
    
    def evaluate_pending_predictions(self, min_age_hours: int = 24) -> List[EvaluationResult]:
        """
        Evaluate all pending predictions that are old enough.
        
        Args:
            min_age_hours: Minimum age in hours before evaluation
            
        Returns:
            List of evaluation results
        """
        try:
            # Get predictions that need evaluation
            recent_predictions = self.predictor_interface.get_recent_predictions(
                hours=min_age_hours * 2  # Look back further to catch pending ones
            )
            
            evaluations = []
            cutoff_time = datetime.now().timestamp() - (min_age_hours * 3600)
            
            for prediction in recent_predictions:
                # Skip if already evaluated
                if prediction.success is not None:
                    continue
                
                # Check if old enough
                try:
                    pred_time = datetime.fromisoformat(prediction.timestamp).timestamp()
                    if pred_time >= cutoff_time:
                        continue  # Too recent
                except ValueError:
                    continue  # Invalid timestamp
                
                # Evaluate this prediction
                evaluation = self.evaluate_prediction(prediction.id)
                if evaluation:
                    evaluations.append(evaluation)
            
            logger.info(f"Evaluated {len(evaluations)} pending predictions")
            return evaluations
            
        except Exception as e:
            logger.error(f"Failed to evaluate pending predictions: {e}")
            return []
    
    def get_accuracy_stats(self) -> Dict:
        """Get prediction accuracy statistics."""
        try:
            stats = self.predictor_interface.get_prediction_accuracy()
            
            # Add evaluation-specific stats
            if self.evaluations_file.exists():
                with open(self.evaluations_file, 'r') as f:
                    evaluations = json.load(f)
                    
                stats["total_evaluations"] = len(evaluations)
                stats["recent_evaluations"] = len([
                    e for e in evaluations 
                    if datetime.fromisoformat(e["timestamp"]) > datetime.now() - timedelta(days=7)
                ])
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get accuracy stats: {e}")
            return {} 