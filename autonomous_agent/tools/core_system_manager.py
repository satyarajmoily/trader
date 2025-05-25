"""Core system manager for safe code replacement and rollback in the Bitcoin predictor."""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from ..chains.code_improver import CodeImprovementResult
from ..tools.code_validator import CodeValidator

logger = logging.getLogger(__name__)


class CoreSystemManager:
    """Manager for safe code replacement in the core Bitcoin prediction system."""
    
    def __init__(self, validator: Optional[CodeValidator] = None):
        """
        Initialize the core system manager.
        
        Args:
            validator: Code validator instance
        """
        self.validator = validator or CodeValidator()
        self.predictor_file = Path("bitcoin_predictor/predictor.py")
        self.backups_dir = Path("backups/predictor_code")
        self.deployment_log = Path("code_deployment_log.json")
        
        # Create backups directory if it doesn't exist
        self.backups_dir.mkdir(parents=True, exist_ok=True)
    
    def create_backup(self, backup_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a backup of the current predictor code.
        
        Args:
            backup_id: Optional custom backup ID
            
        Returns:
            Dict with backup information
        """
        try:
            if not self.predictor_file.exists():
                return {
                    "success": False,
                    "error": "Predictor file not found",
                    "message": f"File {self.predictor_file} does not exist"
                }
            
            # Generate backup ID if not provided
            if not backup_id:
                backup_id = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Create backup file path
            backup_file = self.backups_dir / f"{backup_id}.py"
            
            # Copy the current file
            shutil.copy2(self.predictor_file, backup_file)
            
            # Get file stats
            file_stats = self.predictor_file.stat()
            
            backup_info = {
                "backup_id": backup_id,
                "backup_file": str(backup_file),
                "original_file": str(self.predictor_file),
                "timestamp": datetime.now().isoformat(),
                "file_size": file_stats.st_size,
                "success": True,
                "message": f"Backup created successfully: {backup_id}"
            }
            
            logger.info(f"Created backup {backup_id} at {backup_file}")
            return backup_info
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return {
                "success": False,
                "error": "Backup creation failed",
                "message": str(e)
            }
    
    def restore_backup(self, backup_id: str) -> Dict[str, Any]:
        """
        Restore a previous backup of the predictor code.
        
        Args:
            backup_id: ID of the backup to restore
            
        Returns:
            Dict with restoration results
        """
        try:
            backup_file = self.backups_dir / f"{backup_id}.py"
            
            if not backup_file.exists():
                return {
                    "success": False,
                    "error": "Backup not found",
                    "message": f"Backup {backup_id} does not exist"
                }
            
            # Create a backup of current state before restoration
            current_backup = self.create_backup(f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            
            # Restore the backup
            shutil.copy2(backup_file, self.predictor_file)
            
            restoration_info = {
                "backup_id": backup_id,
                "restored_from": str(backup_file),
                "restored_to": str(self.predictor_file),
                "timestamp": datetime.now().isoformat(),
                "current_backup": current_backup,
                "success": True,
                "message": f"Successfully restored backup {backup_id}"
            }
            
            # Log the restoration
            self._log_deployment({
                "action": "restore",
                "backup_id": backup_id,
                "timestamp": datetime.now().isoformat(),
                "details": restoration_info
            })
            
            logger.info(f"Restored backup {backup_id} to {self.predictor_file}")
            return restoration_info
            
        except Exception as e:
            logger.error(f"Failed to restore backup {backup_id}: {e}")
            return {
                "success": False,
                "error": "Restoration failed",
                "message": str(e)
            }
    
    def deploy_improved_code(self, improvement: CodeImprovementResult, 
                           validate_before_deploy: bool = True) -> Dict[str, Any]:
        """
        Deploy improved code to the core system with safety checks.
        
        Args:
            improvement: Code improvement result to deploy
            validate_before_deploy: Whether to validate code before deployment
            
        Returns:
            Dict with deployment results
        """
        deployment_id = f"deploy_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            # Validate code if requested
            if validate_before_deploy:
                validation_result = self.validator.comprehensive_validation(
                    improvement.improved_code, 
                    test_execution=True
                )
                
                if not validation_result.get("overall_valid", False):
                    return {
                        "deployment_id": deployment_id,
                        "success": False,
                        "error": "Code validation failed",
                        "validation_result": validation_result,
                        "message": "Deployment aborted due to validation failures"
                    }
            
            # Create backup before deployment
            backup_info = self.create_backup(f"pre_deploy_{deployment_id}")
            if not backup_info.get("success", False):
                return {
                    "deployment_id": deployment_id,
                    "success": False,
                    "error": "Backup creation failed",
                    "backup_info": backup_info,
                    "message": "Deployment aborted due to backup failure"
                }
            
            # Read current code
            current_code = self._read_predictor_code()
            
            # Replace the analyze method in the current code
            new_code = self._replace_analyze_method(current_code, improvement.improved_code)
            
            # Write the new code
            with open(self.predictor_file, 'w') as f:
                f.write(new_code)
            
            deployment_info = {
                "deployment_id": deployment_id,
                "improvement_id": improvement.improvement_id,
                "analysis_id": improvement.analysis_id,
                "backup_info": backup_info,
                "timestamp": datetime.now().isoformat(),
                "changes_made": improvement.changes_made,
                "expected_benefits": improvement.expected_benefits,
                "confidence_score": improvement.confidence_score,
                "success": True,
                "message": f"Successfully deployed improvement {improvement.improvement_id}"
            }
            
            # Add validation result if performed
            if validate_before_deploy:
                deployment_info["validation_result"] = validation_result
            
            # Log the deployment
            self._log_deployment({
                "action": "deploy",
                "deployment_id": deployment_id,
                "timestamp": datetime.now().isoformat(),
                "details": deployment_info
            })
            
            logger.info(f"Successfully deployed improvement {improvement.improvement_id}")
            return deployment_info
            
        except Exception as e:
            logger.error(f"Failed to deploy improvement {improvement.improvement_id}: {e}")
            
            # Attempt to restore backup if deployment failed
            if 'backup_info' in locals() and backup_info.get("success", False):
                logger.info("Attempting to restore backup after deployment failure")
                restore_result = self.restore_backup(backup_info["backup_id"])
                
                return {
                    "deployment_id": deployment_id,
                    "success": False,
                    "error": "Deployment failed",
                    "message": str(e),
                    "restore_result": restore_result
                }
            
            return {
                "deployment_id": deployment_id,
                "success": False,
                "error": "Deployment failed",
                "message": str(e)
            }
    
    def _read_predictor_code(self) -> str:
        """Read the current predictor code."""
        try:
            with open(self.predictor_file, 'r') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read predictor code: {e}")
            raise
    
    def _replace_analyze_method(self, original_code: str, new_analyze_method: str) -> str:
        """
        Replace the analyze method in the original code with the new implementation.
        
        Args:
            original_code: Current predictor code
            new_analyze_method: New analyze method implementation
            
        Returns:
            Updated code with new analyze method
        """
        try:
            import ast
            
            # Parse the original code
            tree = ast.parse(original_code)
            lines = original_code.split('\n')
            
            # Find the analyze method
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == "analyze":
                    # Replace the method lines
                    start_line = node.lineno - 1  # Convert to 0-based index
                    end_line = node.end_lineno
                    
                    # Split new method into lines and add proper indentation
                    new_method_lines = new_analyze_method.split('\n')
                    
                    # Replace the old method with the new one
                    new_lines = (lines[:start_line] + 
                               new_method_lines + 
                               lines[end_line:])
                    
                    return '\n'.join(new_lines)
            
            # If analyze method not found, append the new method
            logger.warning("analyze method not found in original code, appending new method")
            return original_code + '\n\n' + new_analyze_method
            
        except Exception as e:
            logger.error(f"Failed to replace analyze method: {e}")
            # Fallback: append the new method
            return original_code + '\n\n# New analyze method:\n' + new_analyze_method
    
    def validate_current_system(self) -> Dict[str, Any]:
        """
        Validate the current core system functionality.
        
        Returns:
            Dict with validation results
        """
        try:
            current_code = self._read_predictor_code()
            
            # Extract analyze method for validation
            analyze_method = self._extract_analyze_method(current_code)
            
            if not analyze_method:
                return {
                    "valid": False,
                    "error": "analyze method not found",
                    "message": "Current system does not contain analyze method"
                }
            
            # Validate the current analyze method
            validation_result = self.validator.comprehensive_validation(
                analyze_method, 
                test_execution=True
            )
            
            return validation_result
            
        except Exception as e:
            return {
                "valid": False,
                "error": "System validation failed",
                "message": str(e)
            }
    
    def _extract_analyze_method(self, code: str) -> Optional[str]:
        """Extract the analyze method from the code."""
        try:
            import ast
            import textwrap
            
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == "analyze":
                    # Get the method code
                    method_lines = code.split('\n')[node.lineno-1:node.end_lineno]
                    method_code = '\n'.join(method_lines)
                    
                    # Remove common indentation to make it standalone
                    dedented_code = textwrap.dedent(method_code)
                    
                    return dedented_code
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to extract analyze method: {e}")
            return None
    
    def get_backup_list(self) -> List[Dict[str, Any]]:
        """
        Get list of available backups.
        
        Returns:
            List of backup information
        """
        try:
            backups = []
            
            for backup_file in self.backups_dir.glob("*.py"):
                backup_id = backup_file.stem
                file_stats = backup_file.stat()
                
                backups.append({
                    "backup_id": backup_id,
                    "file_path": str(backup_file),
                    "created": datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                    "size": file_stats.st_size
                })
            
            # Sort by creation date (newest first)
            backups.sort(key=lambda x: x["created"], reverse=True)
            
            return backups
            
        except Exception as e:
            logger.error(f"Failed to get backup list: {e}")
            return []
    
    def _log_deployment(self, deployment_record: Dict):
        """Log deployment action to deployment log."""
        deployments = []
        
        # Load existing deployments
        if self.deployment_log.exists():
            try:
                with open(self.deployment_log, 'r') as f:
                    deployments = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load existing deployments: {e}")
        
        # Add new deployment
        deployments.append(deployment_record)
        
        # Save back to file
        try:
            with open(self.deployment_log, 'w') as f:
                json.dump(deployments, f, indent=2)
            logger.info(f"Logged deployment action: {deployment_record['action']}")
        except Exception as e:
            logger.error(f"Failed to log deployment: {e}")
    
    def get_deployment_history(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Get deployment history.
        
        Args:
            limit: Maximum number of deployments to return
            
        Returns:
            List of deployment records
        """
        if not self.deployment_log.exists():
            return []
        
        try:
            with open(self.deployment_log, 'r') as f:
                deployments = json.load(f)
            
            if limit:
                return deployments[-limit:]
            return deployments
            
        except Exception as e:
            logger.error(f"Failed to load deployment history: {e}")
            return []
    
    def rollback_last_deployment(self) -> Dict[str, Any]:
        """
        Rollback the last deployment by restoring the most recent backup.
        
        Returns:
            Dict with rollback results
        """
        try:
            # Get deployment history
            deployments = self.get_deployment_history()
            
            # Find the last deployment
            last_deployment = None
            for deployment in reversed(deployments):
                if deployment.get("action") == "deploy":
                    last_deployment = deployment
                    break
            
            if not last_deployment:
                return {
                    "success": False,
                    "error": "No deployment found",
                    "message": "No previous deployment to rollback"
                }
            
            # Get the backup ID from the last deployment
            backup_id = last_deployment.get("details", {}).get("backup_info", {}).get("backup_id")
            
            if not backup_id:
                return {
                    "success": False,
                    "error": "Backup ID not found",
                    "message": "Cannot find backup ID from last deployment"
                }
            
            # Restore the backup
            restore_result = self.restore_backup(backup_id)
            
            if restore_result.get("success", False):
                return {
                    "success": True,
                    "rollback_deployment": last_deployment,
                    "restore_result": restore_result,
                    "message": f"Successfully rolled back to backup {backup_id}"
                }
            else:
                return {
                    "success": False,
                    "error": "Rollback failed",
                    "restore_result": restore_result,
                    "message": "Failed to restore backup during rollback"
                }
                
        except Exception as e:
            logger.error(f"Failed to rollback last deployment: {e}")
            return {
                "success": False,
                "error": "Rollback failed",
                "message": str(e)
            } 