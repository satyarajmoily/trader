"""Storage utilities for prediction records."""

import json
import logging
from pathlib import Path
from typing import List, Optional

from .interfaces import StorageInterface
from .models import PredictionRecord

logger = logging.getLogger(__name__)


class PredictionStorage(StorageInterface):
    """JSON-based storage for prediction records."""
    
    def __init__(self, storage_file: str = "predictions_log.json"):
        """Initialize with storage file path."""
        self.storage_file = Path(storage_file)
        self.ensure_storage_exists()
    
    def ensure_storage_exists(self):
        """Ensure storage file exists with proper structure."""
        if not self.storage_file.exists():
            initial_data = {"predictions": []}
            with open(self.storage_file, 'w') as f:
                json.dump(initial_data, f, indent=2)
            logger.info(f"Created new predictions storage: {self.storage_file}")
    
    def save_prediction(self, prediction: PredictionRecord) -> bool:
        """
        Save a prediction record to storage.
        
        Args:
            prediction: PredictionRecord to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            predictions_data = self._load_storage_data()
            predictions_data["predictions"].append(prediction.to_dict())
            
            with open(self.storage_file, 'w') as f:
                json.dump(predictions_data, f, indent=2)
            
            logger.info(f"Saved prediction {prediction.id} to storage")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save prediction {prediction.id}: {e}")
            return False
    
    def load_predictions(self) -> List[PredictionRecord]:
        """
        Load all prediction records from storage.
        
        Returns:
            List of PredictionRecord objects
        """
        try:
            predictions_data = self._load_storage_data()
            predictions = []
            
            for pred_dict in predictions_data.get("predictions", []):
                try:
                    prediction = PredictionRecord.from_dict(pred_dict)
                    predictions.append(prediction)
                except Exception as e:
                    logger.warning(f"Skipping invalid prediction record: {e}")
                    continue
            
            logger.info(f"Loaded {len(predictions)} predictions from storage")
            return predictions
            
        except Exception as e:
            logger.error(f"Failed to load predictions: {e}")
            return []
    
    def update_prediction(self, prediction_id: str, updates: dict) -> bool:
        """
        Update an existing prediction record.
        
        Args:
            prediction_id: ID of prediction to update
            updates: Dictionary of fields to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            predictions_data = self._load_storage_data()
            predictions = predictions_data.get("predictions", [])
            
            # Find and update the prediction
            updated = False
            for pred_dict in predictions:
                if pred_dict.get("id") == prediction_id:
                    pred_dict.update(updates)
                    updated = True
                    break
            
            if not updated:
                logger.warning(f"Prediction {prediction_id} not found for update")
                return False
            
            # Save back to file
            with open(self.storage_file, 'w') as f:
                json.dump(predictions_data, f, indent=2)
            
            logger.info(f"Updated prediction {prediction_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update prediction {prediction_id}: {e}")
            return False
    
    def get_prediction_by_id(self, prediction_id: str) -> Optional[PredictionRecord]:
        """Get a specific prediction by ID."""
        predictions = self.load_predictions()
        for prediction in predictions:
            if prediction.id == prediction_id:
                return prediction
        return None
    
    def get_recent_predictions(self, limit: int = 10) -> List[PredictionRecord]:
        """Get the most recent predictions."""
        predictions = self.load_predictions()
        # Sort by timestamp (most recent first)
        predictions.sort(key=lambda p: p.timestamp, reverse=True)
        return predictions[:limit]
    
    def _load_storage_data(self) -> dict:
        """Load raw storage data."""
        try:
            with open(self.storage_file, 'r') as f:
                data = json.load(f)
                
            # Handle legacy format (flat list)
            if isinstance(data, list):
                return {"predictions": data}
            
            # Handle proper format
            if isinstance(data, dict) and "predictions" in data:
                return data
            
            # Handle unexpected format
            logger.warning("Unexpected storage format, creating new structure")
            return {"predictions": []}
            
        except Exception as e:
            logger.error(f"Failed to load storage data: {e}")
            return {"predictions": []} 