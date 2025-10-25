"""
GitHub API integration service.
"""
import os
import re
import asyncio
from concurrent.futures import ThreadPoolExecutor
from github import Github
from typing import Tuple, Optional

class GitHubService:
    """Service for fetching GitHub PR diffs."""
    
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        if self.token:
            self.github = Github(self.token)
        else:
            self.github = None
        self.executor = ThreadPoolExecutor(max_workers=5)
    
    async def fetch_pr_diff(self, pr_url: str) -> Tuple[str, str]:
        """
        Fetch PR diff from GitHub URL.
        
        Args:
            pr_url: GitHub PR URL (e.g., https://github.com/owner/repo/pull/123).
            
        Returns:
            Tuple of (diff_content, file_path).
        """
        if not self.github:
            raise Exception("GitHub token not configured. Set GITHUB_TOKEN in .env")
        
        # Parse URL: https://github.com/owner/repo/pull/123
        match = re.match(r"https://github.com/([^/]+)/([^/]+)/pull/(\d+)", pr_url)
        if not match:
            raise ValueError(f"Invalid GitHub PR URL: {pr_url}")
        
        owner, repo_name, pr_number = match.groups()
        return await self.fetch_pr_diff_by_repo(owner, repo_name, int(pr_number))
    
    async def fetch_pr_diff_by_repo(self, owner: str, repo_name: str, pr_number: int) -> Tuple[str, str]:
        """
        Fetch PR diff by repository details.
        
        Args:
            owner: Repository owner.
            repo_name: Repository name.
            pr_number: Pull request number.
            
        Returns:
            Tuple of (diff_content, file_path).
        """
        if not self.github:
            raise Exception("GitHub token not configured. Set GITHUB_TOKEN in .env")
        
        # Run synchronous GitHub API calls in executor
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._fetch_pr_diff_sync,
            owner,
            repo_name,
            pr_number
        )
    
    def _fetch_pr_diff_sync(self, owner: str, repo_name: str, pr_number: int) -> Tuple[str, str]:
        """
        Synchronous method to fetch PR diff.
        
        Args:
            owner: Repository owner.
            repo_name: Repository name.
            pr_number: Pull request number.
            
        Returns:
            Tuple of (diff_content, file_path).
        """
        repo = self.github.get_repo(f"{owner}/{repo_name}")
        pr = repo.get_pull(pr_number)
        
        # Get diff content
        diff_content = pr.diff()
        
        # Get file paths from PR
        files = pr.get_files()
        file_paths = [f.filename for f in files]
        file_path = file_paths[0] if file_paths else "unknown"
        
        return diff_content, file_path

