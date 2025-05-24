"""Configuration management for the Bitcoin Predictor Agent."""

import os
import logging
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration loaded from environment variables."""
    
    # AI Provider Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    
    # GitHub Configuration
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    GITHUB_REPO_OWNER: str = os.getenv("GITHUB_REPO_OWNER", "")
    GITHUB_REPO_NAME: str = os.getenv("GITHUB_REPO_NAME", "bitcoin-predictor")
    
    # Application Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    PREDICTION_INTERVAL_HOURS: int = int(os.getenv("PREDICTION_INTERVAL_HOURS", "24"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    
    # Optional API Keys
    COINGECKO_API_KEY: Optional[str] = os.getenv("COINGECKO_API_KEY")
    
    # File Paths
    PREDICTIONS_LOG_FILE: str = "predictions_log.json"
    LOG_DIR: str = "logs"
    LOG_FILE: str = os.path.join(LOG_DIR, "agent.log")
    
    @classmethod
    def validate(cls) -> bool:
        """Validate that all required configuration is present."""
        required_vars = [
            ("OPENAI_API_KEY", cls.OPENAI_API_KEY),
            ("GITHUB_TOKEN", cls.GITHUB_TOKEN), 
            ("GITHUB_REPO_OWNER", cls.GITHUB_REPO_OWNER),
        ]
        
        missing = [name for name, value in required_vars if not value]
        
        if missing:
            logging.error(f"Missing required environment variables: {missing}")
            return False
            
        return True
    
    @classmethod
    def setup_logging(cls) -> None:
        """Setup application logging configuration."""
        # Ensure log directory exists
        os.makedirs(cls.LOG_DIR, exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, cls.LOG_LEVEL.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(cls.LOG_FILE),
                logging.StreamHandler()
            ]
        )


# Global config instance
config = Config() 