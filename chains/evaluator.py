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

from tools.coingecko_tool import fetch_bitcoin_price_for_date, fetch_current_bitcoin_price

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


class BitcoinPredictionEvaluator:
    """LangChain-based evaluator for Bitcoin predictions."""
    
    def __init__(self, llm: Optional[ChatOpenAI] = None):
        """
        Initialize the prediction evaluator.
        
        Args:
            llm: Optional LLM instance, will create default if not provided
        """
        self.llm = llm or ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            max_tokens=1000
        )
        
        self.evaluation_chain = self._create_evaluation_chain()
        self.predictions_file = Path("predictions_log.json")
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
    "prediction_id": "pred_{prediction_time}",
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
    
    def _load_predictions(self) -> List[Dict]:
        """Load predictions from JSON file."""
        if not self.predictions_file.exists():
            logger.warning("No predictions file found")
            return []
            
        try:
            with open(self.predictions_file, 'r') as f:
                data = json.load(f)
                
                # Handle both flat list and nested structure
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict) and "predictions" in data:
                    return data["predictions"]
                else:
                    logger.warning("Unexpected predictions file format")
                    return []
        except Exception as e:
            logger.error(f"Failed to load predictions: {e}")
            return []
    
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
    
    def _determine_actual_movement(self, old_price: float, new_price: float) -> PredictionResult:
        """Determine actual price movement direction."""
        return "up" if new_price > old_price else "down"
    
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
        Evaluate a specific prediction against current market data.
        
        Args:
            prediction_id: ID of prediction to evaluate
            
        Returns:
            Evaluation result or None if prediction not found
        """
        predictions = self._load_predictions()
        
        # Find the prediction
        prediction_data = None
        for pred in predictions:
            if pred.get("id") == prediction_id:
                prediction_data = pred
                break
                
        if not prediction_data:
            logger.error(f"Prediction {prediction_id} not found")
            return None
        
        try:
            # Get current Bitcoin price
            current_data = fetch_current_bitcoin_price()
            current_price = current_data["price"]
            
            # Calculate price change
            prediction_price = prediction_data["latest_price"]
            price_change_percent = ((current_price - prediction_price) / prediction_price) * 100
            
            # Determine actual movement
            actual_movement = self._determine_actual_movement(prediction_price, current_price)
            
            # Create market context
            market_context = self._create_market_context(price_change_percent)
            
            # Run evaluation chain
            evaluation_input = {
                "prediction": prediction_data["prediction"],
                "prediction_time": prediction_data["timestamp"],
                "prediction_price": prediction_price,
                "current_price": current_price,
                "price_change_percent": price_change_percent,
                "actual_movement": actual_movement,
                "market_context": market_context,
                "timestamp": datetime.now().isoformat()
            }
            
            evaluation = self.evaluation_chain.run(**evaluation_input)
            
            # Save evaluation
            self._save_evaluation(evaluation)
            
            logger.info(f"Evaluated prediction {prediction_id}: {'✅ Correct' if evaluation.is_correct else '❌ Incorrect'}")
            return evaluation
            
        except Exception as e:
            logger.error(f"Failed to evaluate prediction {prediction_id}: {e}")
            return None
    
    def evaluate_pending_predictions(self, min_age_hours: int = 24) -> List[EvaluationResult]:
        """
        Evaluate all predictions that are old enough for evaluation.
        
        Args:
            min_age_hours: Minimum age in hours before a prediction can be evaluated
            
        Returns:
            List of evaluation results
        """
        predictions = self._load_predictions()
        evaluations = []
        
        # Load existing evaluations to avoid duplicates
        existing_evaluations = set()
        if self.evaluations_file.exists():
            try:
                with open(self.evaluations_file, 'r') as f:
                    existing_evals = json.load(f)
                    existing_evaluations = {eval_data["prediction_id"] for eval_data in existing_evals}
            except Exception as e:
                logger.warning(f"Failed to load existing evaluations: {e}")
        
        current_time = datetime.now()
        
        for prediction in predictions:
            prediction_id = prediction.get("id")
            
            # Skip if already evaluated
            if prediction_id in existing_evaluations:
                continue
                
            # Check if prediction is old enough
            try:
                prediction_time = datetime.fromisoformat(prediction["timestamp"])
                age = current_time - prediction_time
                
                if age.total_seconds() >= min_age_hours * 3600:
                    evaluation = self.evaluate_prediction(prediction_id)
                    if evaluation:
                        evaluations.append(evaluation)
                else:
                    logger.debug(f"Prediction {prediction_id} too recent for evaluation")
                    
            except Exception as e:
                logger.error(f"Failed to process prediction {prediction_id}: {e}")
        
        logger.info(f"Completed evaluation of {len(evaluations)} predictions")
        return evaluations
    
    def get_accuracy_stats(self) -> Dict:
        """Get overall prediction accuracy statistics."""
        if not self.evaluations_file.exists():
            return {"total": 0, "correct": 0, "accuracy": 0.0}
        
        try:
            with open(self.evaluations_file, 'r') as f:
                evaluations = json.load(f)
            
            total = len(evaluations)
            correct = sum(1 for eval_data in evaluations if eval_data.get("is_correct", False))
            accuracy = (correct / total) * 100 if total > 0 else 0.0
            
            return {
                "total": total,
                "correct": correct, 
                "incorrect": total - correct,
                "accuracy": accuracy
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate accuracy stats: {e}")
            return {"total": 0, "correct": 0, "accuracy": 0.0}


def create_evaluator(llm: Optional[ChatOpenAI] = None) -> BitcoinPredictionEvaluator:
    """Factory function to create prediction evaluator."""
    return BitcoinPredictionEvaluator(llm=llm)


def evaluate_latest_predictions(min_age_hours: int = 24) -> List[EvaluationResult]:
    """Convenience function to evaluate latest predictions."""
    evaluator = create_evaluator()
    return evaluator.evaluate_pending_predictions(min_age_hours)


if __name__ == "__main__":
    # Test the evaluation system
    print("Testing Bitcoin Prediction Evaluation System")
    print("=" * 50)
    
    evaluator = create_evaluator()
    
    # Check for pending evaluations
    print("Checking for predictions ready for evaluation...")
    evaluations = evaluator.evaluate_pending_predictions(min_age_hours=0)  # 0 for testing
    
    if evaluations:
        print(f"Evaluated {len(evaluations)} predictions:")
        for eval_result in evaluations:
            status = "✅ Correct" if eval_result.is_correct else "❌ Incorrect"
            print(f"- {eval_result.prediction_id}: {status}")
            print(f"  Prediction: {eval_result.prediction}, Actual: {eval_result.actual_movement}")
            print(f"  Price change: {eval_result.price_change_percent:+.2f}%")
    else:
        print("No predictions found or ready for evaluation")
    
    # Show accuracy stats
    stats = evaluator.get_accuracy_stats()
    print(f"\nAccuracy Statistics:")
    print(f"Total Predictions: {stats['total']}")
    print(f"Correct: {stats['correct']}")
    print(f"Accuracy: {stats['accuracy']:.1f}%")
    
    print("\n" + "=" * 50)
    print("✅ Evaluation system test completed!") 