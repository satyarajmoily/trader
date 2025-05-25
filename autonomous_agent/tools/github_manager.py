"""
GitHub Manager Tool for Autonomous Agent

Handles GitHub API integration including:
- PR creation with proper branching
- Repository management
- File updates via GitHub API
- Branch management (always create new branches)
- Error handling for GitHub operations
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from github import Github, GithubException
from github.Repository import Repository
from github.PullRequest import PullRequest
import base64

logger = logging.getLogger(__name__)


class GitHubManager:
    """Manages GitHub operations for autonomous code improvements"""
    
    def __init__(self):
        """Initialize GitHub manager with API credentials"""
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.repo_owner = os.getenv('GITHUB_REPO_OWNER')
        self.repo_name = os.getenv('GITHUB_REPO_NAME')
        
        if not all([self.github_token, self.repo_owner, self.repo_name]):
            raise ValueError(
                "Missing required environment variables: "
                "GITHUB_TOKEN, GITHUB_REPO_OWNER, GITHUB_REPO_NAME"
            )
        
        self.github = Github(self.github_token)
        self.repo = self._get_repository()
        
        logger.info(f"GitHub manager initialized for {self.repo_owner}/{self.repo_name}")
    
    def _get_repository(self) -> Repository:
        """Get the GitHub repository"""
        try:
            repo = self.github.get_repo(f"{self.repo_owner}/{self.repo_name}")
            logger.info(f"Successfully connected to repository: {repo.full_name}")
            return repo
        except GithubException as e:
            logger.error(f"Failed to access repository: {e}")
            raise
    
    def create_improvement_branch(self, improvement_id: str) -> str:
        """
        Create a new branch for code improvement
        Always creates new branches, never commits to main
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        branch_name = f"improvement/{improvement_id}_{timestamp}"
        
        try:
            # Get the default branch (main/master)
            default_branch = self.repo.default_branch
            main_ref = self.repo.get_git_ref(f"heads/{default_branch}")
            main_sha = main_ref.object.sha
            
            # Create new branch from main
            self.repo.create_git_ref(
                ref=f"refs/heads/{branch_name}",
                sha=main_sha
            )
            
            logger.info(f"Created improvement branch: {branch_name}")
            return branch_name
            
        except GithubException as e:
            logger.error(f"Failed to create branch {branch_name}: {e}")
            raise
    
    def update_file_in_branch(
        self, 
        branch_name: str, 
        file_path: str, 
        new_content: str, 
        commit_message: str
    ) -> str:
        """Update a file in the specified branch"""
        try:
            # Get current file content and SHA
            try:
                file_content = self.repo.get_contents(file_path, ref=branch_name)
                sha = file_content.sha
                
                # Update existing file
                result = self.repo.update_file(
                    path=file_path,
                    message=commit_message,
                    content=new_content,
                    sha=sha,
                    branch=branch_name
                )
                
            except GithubException as e:
                if e.status == 404:
                    # File doesn't exist, create it
                    result = self.repo.create_file(
                        path=file_path,
                        message=commit_message,
                        content=new_content,
                        branch=branch_name
                    )
                else:
                    raise
            
            commit_sha = result['commit'].sha
            logger.info(f"Updated file {file_path} in branch {branch_name}: {commit_sha}")
            return commit_sha
            
        except GithubException as e:
            logger.error(f"Failed to update file {file_path}: {e}")
            raise
    
    def create_pull_request(
        self,
        branch_name: str,
        title: str,
        description: str,
        labels: Optional[List[str]] = None
    ) -> PullRequest:
        """Create a pull request from improvement branch to main"""
        try:
            pr = self.repo.create_pull(
                title=title,
                body=description,
                head=branch_name,
                base=self.repo.default_branch
            )
            
            # Add labels if provided
            if labels:
                pr.add_to_labels(*labels)
            
            logger.info(f"Created PR #{pr.number}: {title}")
            return pr
            
        except GithubException as e:
            logger.error(f"Failed to create PR from {branch_name}: {e}")
            raise
    
    def get_pull_request_status(self, pr_number: int) -> Dict[str, Any]:
        """Get status information for a pull request"""
        try:
            pr = self.repo.get_pull(pr_number)
            
            status = {
                'number': pr.number,
                'title': pr.title,
                'state': pr.state,
                'merged': pr.merged,
                'mergeable': pr.mergeable,
                'head_branch': pr.head.ref,
                'base_branch': pr.base.ref,
                'created_at': pr.created_at.isoformat(),
                'url': pr.html_url,
                'author': pr.user.login,
                'commits': pr.commits,
                'additions': pr.additions,
                'deletions': pr.deletions,
                'changed_files': pr.changed_files
            }
            
            # Get review status
            reviews = list(pr.get_reviews())
            status['reviews'] = [
                {
                    'user': review.user.login,
                    'state': review.state,
                    'submitted_at': review.submitted_at.isoformat() if review.submitted_at else None
                }
                for review in reviews
            ]
            
            return status
            
        except GithubException as e:
            logger.error(f"Failed to get PR status for #{pr_number}: {e}")
            raise
    
    def list_open_prs(self, label_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """List open pull requests, optionally filtered by label"""
        try:
            prs = self.repo.get_pulls(state='open')
            
            pr_list = []
            for pr in prs:
                # Filter by label if specified
                if label_filter:
                    pr_labels = [label.name for label in pr.labels]
                    if label_filter not in pr_labels:
                        continue
                
                pr_list.append({
                    'number': pr.number,
                    'title': pr.title,
                    'head_branch': pr.head.ref,
                    'created_at': pr.created_at.isoformat(),
                    'url': pr.html_url,
                    'labels': [label.name for label in pr.labels]
                })
            
            return pr_list
            
        except GithubException as e:
            logger.error(f"Failed to list open PRs: {e}")
            raise
    
    def delete_branch(self, branch_name: str) -> bool:
        """Delete a branch (cleanup after PR merge)"""
        try:
            ref = self.repo.get_git_ref(f"heads/{branch_name}")
            ref.delete()
            logger.info(f"Deleted branch: {branch_name}")
            return True
            
        except GithubException as e:
            logger.error(f"Failed to delete branch {branch_name}: {e}")
            return False
    
    def validate_access(self) -> Dict[str, Any]:
        """Validate GitHub access and permissions"""
        try:
            repo_info = {
                'name': self.repo.name,
                'full_name': self.repo.full_name,
                'private': self.repo.private,
                'default_branch': self.repo.default_branch,
                'permissions': {
                    'admin': self.repo.permissions.admin,
                    'push': self.repo.permissions.push,
                    'pull': self.repo.permissions.pull
                }
            }
            
            # Test rate limit
            rate_limit = self.github.get_rate_limit()
            repo_info['rate_limit'] = {
                'remaining': rate_limit.core.remaining,
                'limit': rate_limit.core.limit,
                'reset': rate_limit.core.reset.isoformat()
            }
            
            logger.info("GitHub access validation successful")
            return repo_info
            
        except GithubException as e:
            logger.error(f"GitHub access validation failed: {e}")
            raise


def test_github_manager() -> bool:
    """Test GitHub manager functionality"""
    try:
        manager = GitHubManager()
        
        print("🔧 Testing GitHub Manager...")
        
        # Test access validation
        repo_info = manager.validate_access()
        print(f"✅ Repository access: {repo_info['full_name']}")
        print(f"✅ Permissions: {repo_info['permissions']}")
        print(f"✅ Rate limit: {repo_info['rate_limit']['remaining']}/{repo_info['rate_limit']['limit']}")
        
        # Test listing PRs
        open_prs = manager.list_open_prs()
        print(f"✅ Open PRs: {len(open_prs)}")
        
        return True
        
    except Exception as e:
        print(f"❌ GitHub manager test failed: {e}")
        return False


if __name__ == "__main__":
    test_github_manager() 