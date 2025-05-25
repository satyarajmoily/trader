"""Interface for agent to interact with the core prediction system."""

from typing import List, Optional, Dict, Any
from datetime import datetime
import sys
import os

# Add the parent directory to path so we can import bitcoin_predictor
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from bitcoin_predictor import BitcoinPredictor, PredictionStorage, PredictionRecord


class PredictorInterface:
    """
    Clean interface for the autonomous agent to interact with the core prediction system.
    
    This interface provides a clean abstraction layer between the agent and the
    core bitcoin predictor, making it easy to swap out either system.
    """
    
    def __init__(self):
        """Initialize the predictor interface."""
        self.predictor = None  # Will be initialized with timeframe
        self.storage = PredictionStorage()
    
    def make_prediction(self, data_source: Optional[str] = None, timeframe: str = "1d") -> Dict[str, Any]:
        """
        Make a Bitcoin price prediction.
        
        Args:
            data_source: Optional data source path
            timeframe: Time interval for prediction (1m, 5m, 15m, 1h, 4h, 1d)
            
        Returns:
            Dict with prediction result and metadata
        """
        try:
            # Initialize predictor with timeframe if not already done or timeframe changed
            if self.predictor is None or getattr(self.predictor, 'timeframe', None) != timeframe:
                self.predictor = BitcoinPredictor(timeframe=timeframe)
            
            prediction = self.predictor.predict(data_source)
            return {
                "success": True,
                "prediction": prediction.to_dict(),
                "message": f"Prediction {prediction.id} generated successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Prediction failed: {e}"
            }
    
    def get_recent_predictions(self, hours: int = 24) -> List[PredictionRecord]:
        """
        Get recent predictions for evaluation.
        
        Args:
            hours: How many hours back to look for predictions
            
        Returns:
            List of recent PredictionRecord objects
        """
        all_predictions = self.storage.load_predictions()
        
        # Filter by time window if specified
        if hours > 0:
            cutoff_time = datetime.now().timestamp() - (hours * 3600)
            recent_predictions = []
            
            for pred in all_predictions:
                try:
                    pred_time = datetime.fromisoformat(pred.timestamp).timestamp()
                    if pred_time >= cutoff_time:
                        recent_predictions.append(pred)
                except ValueError:
                    # Skip predictions with invalid timestamps
                    continue
            
            return recent_predictions
        
        return all_predictions
    
    def update_prediction_outcome(self, prediction_id: str, 
                                actual_outcome: str, 
                                actual_price: float,
                                evaluation_timestamp: Optional[str] = None) -> bool:
        """
        Update a prediction with actual outcome data.
        
        Args:
            prediction_id: ID of the prediction to update
            actual_outcome: "up" or "down" - actual market movement
            actual_price: Actual Bitcoin price
            evaluation_timestamp: When the evaluation was done
            
        Returns:
            True if successful, False otherwise
        """
        updates = {
            "actual_outcome": actual_outcome,
            "actual_price": actual_price,
            "evaluation_timestamp": evaluation_timestamp or datetime.now().isoformat()
        }
        
        # Determine if prediction was successful
        prediction = self.storage.get_prediction_by_id(prediction_id)
        if prediction:
            updates["success"] = (prediction.prediction == actual_outcome)
        
        return self.storage.update_prediction(prediction_id, updates)
    
    def get_failed_predictions(self, limit: int = 10) -> List[PredictionRecord]:
        """
        Get recent failed predictions for improvement analysis.
        
        Args:
            limit: Maximum number of failed predictions to return
            
        Returns:
            List of failed PredictionRecord objects
        """
        all_predictions = self.storage.load_predictions()
        failed_predictions = [
            pred for pred in all_predictions 
            if pred.success is False
        ]
        
        # Sort by timestamp (most recent first)
        failed_predictions.sort(
            key=lambda p: p.timestamp, 
            reverse=True
        )
        
        return failed_predictions[:limit]
    
    def get_prediction_accuracy(self, days: int = 30) -> Dict[str, Any]:
        """
        Get prediction accuracy statistics.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dict with accuracy statistics
        """
        predictions = self.get_recent_predictions(days * 24)
        
        if not predictions:
            return {
                "total_predictions": 0,
                "evaluated_predictions": 0,
                "accuracy": 0.0,
                "success_rate": 0.0
            }
        
        evaluated = [p for p in predictions if p.success is not None]
        successful = [p for p in evaluated if p.success is True]
        
        total_predictions = len(predictions)
        evaluated_predictions = len(evaluated)
        accuracy = len(successful) / len(evaluated) if evaluated else 0.0
        
        return {
            "total_predictions": total_predictions,
            "evaluated_predictions": evaluated_predictions,
            "successful_predictions": len(successful),
            "accuracy": accuracy,
            "success_rate": accuracy * 100
        }
    
    def validate_predictor_code(self, code: str) -> Dict[str, Any]:
        """
        Validate new predictor code (placeholder for future implementation).
        
        Args:
            code: New predictor code to validate
            
        Returns:
            Dict with validation results
        """
        # TODO: Implement code validation logic for Phase 3
        return {
            "valid": True,
            "message": "Code validation not yet implemented"
        }
    
    def update_predictor_code(self, new_code: str) -> Dict[str, Any]:
        """
        Update the predictor code (placeholder for future implementation).
        
        Args:
            new_code: New predictor code
            
        Returns:
            Dict with update results
        """
        # TODO: Implement code update logic for Phase 3
        return {
            "success": False,
            "message": "Code update not yet implemented (Phase 3 feature)"
        } 