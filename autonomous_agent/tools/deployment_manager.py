"""
Enhanced Deployment Manager for Autonomous Agent

Handles different deployment modes:
- Production: Full PR workflow with human review
- Local: Simulated CI/CD with auto-merge and restart
- Demo: Fast automated cycle for demonstration

This implements the PR-first approach where all changes go through version control.
"""

import os
import sys
import json
import logging
import subprocess
import signal
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Literal
from enum import Enum

from .github_manager import GitHubManager
from .core_system_manager import CoreSystemManager
from ..chains.code_improver import CodeImprovementResult

logger = logging.getLogger(__name__)


class DeploymentMode(Enum):
    """Deployment modes for the autonomous agent."""
    PRODUCTION = "production"
    STAGING = "staging"
    LOCAL = "local"
    DEMO = "demo"


class LocalGitManager:
    """Manages local git operations for simulated CI/CD."""
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
        self.ensure_git_repo()
    
    def ensure_git_repo(self):
        """Ensure we're in a git repository."""
        git_dir = self.repo_path / ".git"
        if not git_dir.exists():
            logger.warning("Not in a git repository - autonomous commits will be skipped")
    
    def create_improvement_branch(self, improvement_id: str) -> str:
        """Create a new branch for the improvement."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        branch_name = f"improvement/{improvement_id}_{timestamp}"
        
        try:
            # Create and checkout new branch
            subprocess.run(
                ["git", "checkout", "-b", branch_name],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )
            
            logger.info(f"Created local improvement branch: {branch_name}")
            return branch_name
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create branch {branch_name}: {e}")
            raise
    
    def commit_improvement(
        self, 
        branch_name: str, 
        file_paths: List[str], 
        commit_message: str
    ) -> str:
        """Commit improvements to the branch."""
        try:
            # Add files
            for file_path in file_paths:
                subprocess.run(
                    ["git", "add", file_path],
                    cwd=self.repo_path,
                    check=True
                )
            
            # Commit changes
            result = subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
                text=True
            )
            
            # Get commit hash
            commit_hash = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
                text=True
            ).stdout.strip()
            
            logger.info(f"Committed improvement to {branch_name}: {commit_hash}")
            return commit_hash
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to commit to {branch_name}: {e}")
            raise
    
    def auto_merge_to_main(self, branch_name: str) -> bool:
        """Auto-merge branch to main for local testing."""
        try:
            # Switch to main
            subprocess.run(
                ["git", "checkout", "main"],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )
            
            # Merge branch
            subprocess.run(
                ["git", "merge", branch_name, "--no-ff"],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )
            
            # Delete the feature branch
            subprocess.run(
                ["git", "branch", "-d", branch_name],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )
            
            logger.info(f"Auto-merged {branch_name} to main")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to auto-merge {branch_name}: {e}")
            return False


class ProcessRestartManager:
    """Manages graceful process restart for code deployment."""
    
    def __init__(self):
        self.restart_script = None
        self.current_process_id = os.getpid()
    
    def schedule_restart(self, delay_seconds: int = 5) -> bool:
        """Schedule a graceful restart of the current process."""
        try:
            # Create restart script
            restart_script = self._create_restart_script()
            
            # Schedule restart
            logger.info(f"Scheduling restart in {delay_seconds} seconds...")
            
            # Use a separate process to restart us
            subprocess.Popen([
                sys.executable, restart_script, 
                str(self.current_process_id), 
                str(delay_seconds)
            ])
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to schedule restart: {e}")
            return False
    
    def _create_restart_script(self) -> str:
        """Create a temporary restart script."""
        restart_script = Path("restart_agent.py")
        
        script_content = '''#!/usr/bin/env python3
import sys
import time
import os
import signal
import subprocess

def main():
    if len(sys.argv) != 3:
        print("Usage: restart_agent.py <pid> <delay>")
        sys.exit(1)
    
    old_pid = int(sys.argv[1])
    delay = int(sys.argv[2])
    
    print(f"Waiting {delay} seconds before restart...")
    time.sleep(delay)
    
    # Gracefully terminate old process
    try:
        os.kill(old_pid, signal.SIGTERM)
        time.sleep(2)
    except ProcessLookupError:
        pass  # Process already ended
    
    # Restart with same arguments
    print("Restarting autonomous agent...")
    os.execv(sys.executable, [sys.executable] + sys.argv[3:] if len(sys.argv) > 3 else [sys.executable, "main.py", "agent", "autonomous", "--mode", "local"])

if __name__ == "__main__":
    main()
'''
        
        with open(restart_script, 'w') as f:
            f.write(script_content)
        
        # Make executable
        os.chmod(restart_script, 0o755)
        
        return str(restart_script)


class EnhancedDeploymentManager:
    """
    Enhanced deployment manager supporting multiple deployment modes.
    
    Implements the PR-first approach with different execution modes:
    - Production: Create PR, wait for human review, deploy via CI/CD
    - Local: Create PR, auto-merge, deploy locally, restart process
    - Demo: Fast cycle for demonstration purposes
    """
    
    def __init__(self, mode: DeploymentMode = DeploymentMode.LOCAL):
        self.mode = mode
        self.core_manager = CoreSystemManager()
        self.local_git = LocalGitManager()
        self.restart_manager = ProcessRestartManager()
        
        # Initialize GitHub manager for production/staging modes
        self.github_manager = None
        if mode in [DeploymentMode.PRODUCTION, DeploymentMode.STAGING]:
            try:
                self.github_manager = GitHubManager()
            except Exception as e:
                logger.warning(f"GitHub manager not available: {e}")
        
        logger.info(f"Deployment manager initialized in {mode.value} mode")
    
    def deploy_improvement(
        self, 
        improvement: CodeImprovementResult,
        auto_restart: bool = True
    ) -> Dict[str, Any]:
        """
        Deploy improvement using the appropriate mode workflow.
        
        Args:
            improvement: The improvement to deploy
            auto_restart: Whether to restart the process after deployment
            
        Returns:
            Dict with deployment results
        """
        if self.mode == DeploymentMode.PRODUCTION:
            return self._production_deployment(improvement)
        elif self.mode == DeploymentMode.STAGING:
            return self._staging_deployment(improvement)
        elif self.mode == DeploymentMode.LOCAL:
            return self._local_deployment(improvement, auto_restart)
        elif self.mode == DeploymentMode.DEMO:
            return self._demo_deployment(improvement, auto_restart)
        else:
            raise ValueError(f"Unknown deployment mode: {self.mode}")
    
    def _production_deployment(self, improvement: CodeImprovementResult) -> Dict[str, Any]:
        """Production deployment: Create PR and wait for human review."""
        try:
            if not self.github_manager:
                return {
                    "success": False,
                    "error": "GitHub manager not available",
                    "message": "Cannot create PR in production mode without GitHub access"
                }
            
            # Create improvement branch
            branch_name = self.github_manager.create_improvement_branch(improvement.improvement_id)
            
            # Update file in branch
            commit_message = f"🤖 Autonomous improvement: {improvement.improvement_id}"
            commit_sha = self.github_manager.update_file_in_branch(
                branch_name=branch_name,
                file_path="bitcoin_predictor/predictor.py",
                new_content=self._generate_full_file_content(improvement),
                commit_message=commit_message
            )
            
            # Create PR
            pr_title = f"🤖 Autonomous Improvement: {improvement.improvement_id}"
            pr_description = self._generate_pr_description(improvement)
            
            pr = self.github_manager.create_pull_request(
                branch_name=branch_name,
                title=pr_title,
                description=pr_description,
                labels=["autonomous-improvement", "production"]
            )
            
            return {
                "success": True,
                "mode": "production",
                "improvement_id": improvement.improvement_id,
                "branch_name": branch_name,
                "commit_sha": commit_sha,
                "pr_number": pr.number,
                "pr_url": pr.html_url,
                "message": f"✅ Production PR created: #{pr.number}",
                "next_steps": "Wait for human review and merge"
            }
            
        except Exception as e:
            logger.error(f"Production deployment failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"❌ Production deployment failed: {e}"
            }
    
    def _staging_deployment(self, improvement: CodeImprovementResult) -> Dict[str, Any]:
        """Staging deployment: Create PR with auto-merge option."""
        # Similar to production but may have auto-merge enabled
        result = self._production_deployment(improvement)
        if result["success"]:
            result["mode"] = "staging"
            result["message"] = f"✅ Staging PR created: #{result['pr_number']}"
        return result
    
    def _local_deployment(
        self, 
        improvement: CodeImprovementResult, 
        auto_restart: bool = True
    ) -> Dict[str, Any]:
        """Local deployment: Git branch, commit, auto-merge, deploy, restart."""
        try:
            deployment_id = f"local_deploy_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Step 1: Create local git branch
            branch_name = self.local_git.create_improvement_branch(improvement.improvement_id)
            
            # Step 2: Deploy code locally first
            local_deploy_result = self.core_manager.deploy_improved_code(
                improvement, validate_before_deploy=True
            )
            
            if not local_deploy_result.get("success", False):
                return {
                    "success": False,
                    "error": "Local code deployment failed",
                    "deployment_result": local_deploy_result,
                    "message": f"❌ Failed to deploy code locally: {local_deploy_result.get('error', 'Unknown error')}"
                }
            
            # Step 3: Commit the changes
            commit_message = f"🤖 Local autonomous improvement: {improvement.improvement_id}\n\n{improvement.improvement_description}"
            commit_hash = self.local_git.commit_improvement(
                branch_name=branch_name,
                file_paths=["bitcoin_predictor/predictor.py"],
                commit_message=commit_message
            )
            
            # Step 4: Auto-merge to main
            merge_success = self.local_git.auto_merge_to_main(branch_name)
            
            # Step 5: Schedule restart if requested
            restart_scheduled = False
            if auto_restart:
                restart_scheduled = self.restart_manager.schedule_restart(delay_seconds=3)
            
            result = {
                "success": True,
                "mode": "local",
                "deployment_id": deployment_id,
                "improvement_id": improvement.improvement_id,
                "branch_name": branch_name,
                "commit_hash": commit_hash,
                "merge_success": merge_success,
                "restart_scheduled": restart_scheduled,
                "local_deployment": local_deploy_result,
                "message": f"✅ Local deployment complete: {improvement.improvement_id}"
            }
            
            if restart_scheduled:
                result["message"] += " (restarting in 3 seconds)"
            
            return result
            
        except Exception as e:
            logger.error(f"Local deployment failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"❌ Local deployment failed: {e}"
            }
    
    def _demo_deployment(
        self, 
        improvement: CodeImprovementResult, 
        auto_restart: bool = True
    ) -> Dict[str, Any]:
        """Demo deployment: Fast local deployment for demonstration."""
        # Demo mode is similar to local but with minimal delays
        result = self._local_deployment(improvement, auto_restart)
        if result["success"]:
            result["mode"] = "demo"
            result["message"] = result["message"].replace("Local", "Demo")
        return result
    
    def _generate_full_file_content(self, improvement: CodeImprovementResult) -> str:
        """Generate the full file content with the improvement applied."""
        # Read current predictor file
        predictor_file = Path("bitcoin_predictor/predictor.py")
        current_content = predictor_file.read_text()
        
        # Apply the improvement (this would need to be more sophisticated)
        # For now, we'll use the core system manager's logic
        return self.core_manager._replace_analyze_method(current_content, improvement.improved_code)
    
    def _generate_pr_description(self, improvement: CodeImprovementResult) -> str:
        """Generate comprehensive PR description."""
        description = f"""## 🤖 Autonomous Agent Code Improvement

**Improvement ID:** `{improvement.improvement_id}`  
**Analysis ID:** `{improvement.analysis_id}`  
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

### 📊 Failed Prediction Analysis
{improvement.improvement_description}

### 🔧 Changes Made
"""
        
        for i, change in enumerate(improvement.changes_made, 1):
            description += f"{i}. {change}\n"
        
        description += "\n### ✨ Expected Benefits\n"
        
        for i, benefit in enumerate(improvement.expected_benefits, 1):
            description += f"{i}. {benefit}\n"
        
        description += f"""
### 🎯 Confidence Score
**{improvement.confidence_score:.2f}** (0.0 = low confidence, 1.0 = high confidence)

### 🤖 Autonomous Agent Information
- **Agent Version:** Phase 5 Production
- **Deployment Mode:** {self.mode.value}
- **Generated by:** Bitcoin Prediction Autonomous Agent

---
*This PR was created automatically by the autonomous agent system. Please review the changes carefully before merging.*
"""
        
        return description
    
    def get_deployment_status(self) -> Dict[str, Any]:
        """Get current deployment status and configuration."""
        return {
            "mode": self.mode.value,
            "github_available": self.github_manager is not None,
            "git_repo_available": (Path(".git").exists()),
            "core_manager_ready": self.core_manager is not None,
            "restart_manager_ready": self.restart_manager is not None,
            "current_process_id": os.getpid()
        } 