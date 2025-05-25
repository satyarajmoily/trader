"""
Environment Management for Bitcoin Predictor System

Handles environment configuration, secrets management, and deployment environments.
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)

@dataclass
class EnvironmentConfig:
    """Environment configuration data."""
    name: str
    description: str
    variables: Dict[str, str]
    secrets: List[str]
    required_services: List[str]

class EnvironmentManager:
    """
    Environment management for Bitcoin Predictor deployments.
    
    Handles configuration for different deployment environments:
    - Development
    - Staging  
    - Production
    """
    
    def __init__(self, config_dir: str = "deployment/env"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Default environment configurations
        self.environments = {
            "development": EnvironmentConfig(
                name="development",
                description="Local development environment",
                variables={
                    "ENVIRONMENT": "development",
                    "LOG_LEVEL": "DEBUG",
                    "PREDICTION_INTERVAL": "1h",
                    "ENABLE_MONITORING": "false",
                    "REDIS_ENABLED": "false"
                },
                secrets=["OPENAI_API_KEY", "GITHUB_TOKEN"],
                required_services=["core", "agent"]
            ),
            "staging": EnvironmentConfig(
                name="staging",
                description="Staging environment for testing",
                variables={
                    "ENVIRONMENT": "staging",
                    "LOG_LEVEL": "INFO",
                    "PREDICTION_INTERVAL": "4h",
                    "ENABLE_MONITORING": "true",
                    "REDIS_ENABLED": "true"
                },
                secrets=["OPENAI_API_KEY", "GITHUB_TOKEN", "COINGECKO_API_KEY"],
                required_services=["core", "agent", "redis", "monitor"]
            ),
            "production": EnvironmentConfig(
                name="production",
                description="Production environment",
                variables={
                    "ENVIRONMENT": "production",
                    "LOG_LEVEL": "INFO",
                    "PREDICTION_INTERVAL": "1d",
                    "ENABLE_MONITORING": "true",
                    "REDIS_ENABLED": "true",
                    "ENABLE_ALERTING": "true"
                },
                secrets=["OPENAI_API_KEY", "GITHUB_TOKEN", "COINGECKO_API_KEY"],
                required_services=["core", "agent", "redis", "monitor", "elasticsearch", "kibana"]
            )
        }
    
    def create_env_file(self, environment: str, output_file: Optional[str] = None) -> str:
        """Create environment file for specified environment."""
        if environment not in self.environments:
            raise ValueError(f"Unknown environment: {environment}")
        
        config = self.environments[environment]
        
        if output_file is None:
            output_file = self.config_dir / f"{environment}.env"
        else:
            output_file = Path(output_file)
        
        # Create environment file content
        env_content = [
            f"# {config.description}",
            f"# Generated on {os.environ.get('USER', 'unknown')}@{os.uname().nodename}",
            "",
            "# Environment Configuration"
        ]
        
        # Add environment variables
        for key, value in config.variables.items():
            env_content.append(f"{key}={value}")
        
        env_content.append("")
        env_content.append("# Secrets (set these manually)")
        
        # Add secret placeholders
        for secret in config.secrets:
            current_value = os.getenv(secret, "")
            if current_value:
                env_content.append(f"{secret}={current_value}")
            else:
                env_content.append(f"# {secret}=your-{secret.lower().replace('_', '-')}-here")
        
        # Write to file
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            f.write('\n'.join(env_content))
        
        logger.info(f"Environment file created: {output_file}")
        return str(output_file)
    
    def validate_environment(self, environment: str) -> Dict[str, Any]:
        """Validate environment configuration."""
        if environment not in self.environments:
            return {"valid": False, "error": f"Unknown environment: {environment}"}
        
        config = self.environments[environment]
        validation_result = {
            "valid": True,
            "environment": environment,
            "missing_secrets": [],
            "warnings": [],
            "info": []
        }
        
        # Check required secrets
        for secret in config.secrets:
            if not os.getenv(secret):
                validation_result["missing_secrets"].append(secret)
        
        if validation_result["missing_secrets"]:
            validation_result["valid"] = False
        
        # Environment-specific validations
        if environment == "production":
            # Production-specific checks
            if not os.getenv("COINGECKO_API_KEY"):
                validation_result["warnings"].append(
                    "COINGECKO_API_KEY not set - may hit rate limits"
                )
            
            validation_result["info"].append(
                "Production environment requires all services to be healthy"
            )
        
        elif environment == "development":
            validation_result["info"].append(
                "Development environment uses minimal services"
            )
        
        return validation_result
    
    def get_environment_info(self, environment: str) -> Dict[str, Any]:
        """Get detailed information about an environment."""
        if environment not in self.environments:
            return {"error": f"Unknown environment: {environment}"}
        
        config = self.environments[environment]
        
        return {
            "name": config.name,
            "description": config.description,
            "variables": config.variables,
            "secrets": config.secrets,
            "required_services": config.required_services,
            "env_file_path": str(self.config_dir / f"{environment}.env")
        }
    
    def list_environments(self) -> List[Dict[str, Any]]:
        """List all available environments."""
        return [
            {
                "name": name,
                "description": config.description,
                "services": len(config.required_services),
                "secrets": len(config.secrets)
            }
            for name, config in self.environments.items()
        ]
    
    def setup_environment(self, environment: str) -> bool:
        """Setup environment with all necessary files and validation."""
        try:
            logger.info(f"Setting up {environment} environment...")
            
            # Create environment file
            env_file = self.create_env_file(environment)
            
            # Validate configuration
            validation = self.validate_environment(environment)
            
            if not validation["valid"]:
                logger.error(f"Environment validation failed: {validation}")
                return False
            
            # Log warnings
            for warning in validation.get("warnings", []):
                logger.warning(warning)
            
            # Log info
            for info in validation.get("info", []):
                logger.info(info)
            
            logger.info(f"Environment {environment} setup completed")
            logger.info(f"Environment file: {env_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup environment {environment}: {e}")
            return False
    
    def export_environment_config(self, environment: str, output_file: str) -> bool:
        """Export environment configuration to JSON file."""
        try:
            if environment not in self.environments:
                raise ValueError(f"Unknown environment: {environment}")
            
            config = self.environments[environment]
            
            export_data = {
                "environment": environment,
                "config": {
                    "name": config.name,
                    "description": config.description,
                    "variables": config.variables,
                    "secrets": config.secrets,
                    "required_services": config.required_services
                },
                "validation": self.validate_environment(environment),
                "export_timestamp": os.environ.get("USER", "unknown")
            }
            
            with open(output_file, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            logger.info(f"Environment config exported to: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export environment config: {e}")
            return False 