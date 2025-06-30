"""
Git operations module for MCP tool.
Handles repository cloning, pushing changes, and Git repository management using GitPython.
"""

import os
import re
from pathlib import Path
from urllib.parse import urlparse
import git
from git import Repo, InvalidGitRepositoryError, GitCommandError
from github import Github, GithubException
from .config import MCPConfig
from .logger import get_logger


class GitOperations:
    """Git operations manager for MCP tool."""
    
    def __init__(self, verbose=False):
        """
        Initialize Git operations manager.
        
        Args:
            verbose (bool): Enable verbose logging
        """
        self.logger = get_logger(verbose=verbose)
        self.config = MCPConfig(verbose=verbose)
    
    def is_valid_repo_url(self, url):
        """
        Validate GitHub repository URL.
        
        Args:
            url (str): Repository URL to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            parsed = urlparse(url)
            
            # Check if it's a GitHub URL
            if parsed.netloc not in ['github.com', 'www.github.com']:
                return False
            
            # Check path format (should be /username/repo or /username/repo.git)
            path_parts = parsed.path.strip('/').split('/')
            if len(path_parts) < 2:
                return False
            
            # Basic validation of username and repo name
            username, repo = path_parts[0], path_parts[1]
            if not username or not repo:
                return False
            
            # Remove .git suffix if present
            if repo.endswith('.git'):
                repo = repo[:-4]
            
            # Check for valid characters (GitHub allows alphanumeric, hyphens, underscores, dots)
            valid_pattern = re.compile(r'^[a-zA-Z0-9._-]+$')
            if not valid_pattern.match(username) or not valid_pattern.match(repo):
                return False
            
            return True
            
        except Exception:
            return False
    
    def is_git_repository(self, path):
        """
        Check if path is a valid Git repository.
        
        Args:
            path (str): Path to check
            
        Returns:
            bool: True if valid Git repository, False otherwise
        """
        try:
            Repo(path)
            return True
        except InvalidGitRepositoryError:
            return False
        except Exception:
            return False
    
    def clone_repository(self, repo_url, local_path, dry_run=False):
        """
        Clone a GitHub repository to local path.
        
        Args:
            repo_url (str): GitHub repository URL
            local_path (str): Local path to clone to
            dry_run (bool): If True, simulate operation without making changes
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Validate repository URL
            if not self.is_valid_repo_url(repo_url):
                self.logger.error(f"Invalid repository URL: {repo_url}")
                return False
            
            local_path_obj = Path(local_path)
            
            # Check if local path already exists
            if local_path_obj.exists():
                if local_path_obj.is_dir() and any(local_path_obj.iterdir()):
                    if self.is_git_repository(local_path):
                        self.logger.warning(f"Directory {local_path} already contains a Git repository")
                    else:
                        self.logger.warning(f"Directory {local_path} is not empty")
                    
                    response = input(f"Directory {local_path} already exists. Continue anyway? (y/N): ")
                    if response.lower() != 'y':
                        self.logger.info("Clone operation cancelled.")
                        return False
                elif local_path_obj.is_file():
                    self.logger.error(f"Path {local_path} exists and is a file, not a directory")
                    return False
            
            if dry_run:
                self.logger.info(f"[DRY RUN] Would clone {repo_url} to {local_path}")
                return True
            
            # Create parent directories if needed
            local_path_obj.parent.mkdir(parents=True, exist_ok=True)
            
            self.logger.info(f"Cloning repository {repo_url} to {local_path}...")
            
            # Clone the repository
            repo = Repo.clone_from(repo_url, local_path)
            
            self.logger.info(f"Successfully cloned repository to {local_path}")
            return True
            
        except GitCommandError as e:
            if "Authentication failed" in str(e) or "access denied" in str(e).lower():
                self.logger.error("Authentication failed. Please check your GitHub token.")
            elif "not found" in str(e).lower():
                self.logger.error(f"Repository not found: {repo_url}")
            else:
                self.logger.error(f"Git error during clone: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to clone repository: {e}")
            return False
    
    def push_changes(self, local_path, commit_message, dry_run=False):
        """
        Push changes from local repository to GitHub.
        
        Args:
            local_path (str): Path to local Git repository
            commit_message (str): Commit message
            dry_run (bool): If True, simulate operation without making changes
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Validate local path is a Git repository
            if not self.is_git_repository(local_path):
                self.logger.error(f"Path {local_path} is not a valid Git repository")
                return False
            
            repo = Repo(local_path)
            
            # Check if there are any changes to commit
            if not repo.is_dirty() and not repo.untracked_files:
                self.logger.info("No changes to commit")
                return True
            
            if dry_run:
                self.logger.info(f"[DRY RUN] Would stage all changes and commit with message: '{commit_message}'")
                self.logger.info(f"[DRY RUN] Would push to remote repository")
                return True
            
            # Stage all changes
            repo.git.add(A=True)
            self.logger.info("Staged all changes")
            
            # Commit changes
            repo.index.commit(commit_message)
            self.logger.info(f"Committed changes with message: '{commit_message}'")
            
            # Get default branch
            default_branch = self.config.get_default_branch()
            
            # Push to remote
            origin = repo.remote('origin')
            
            # Configure authentication if token is available
            github_token = self.config.get_github_token()
            if github_token:
                # Update remote URL to include token for authentication
                remote_url = origin.url
                if remote_url.startswith('https://github.com/'):
                    auth_url = remote_url.replace('https://github.com/', f'https://{github_token}@github.com/')
                    origin.set_url(auth_url)
            
            self.logger.info(f"Pushing changes to remote repository...")
            origin.push(default_branch)
            
            self.logger.info("Successfully pushed changes to GitHub")
            return True
            
        except GitCommandError as e:
            if "Authentication failed" in str(e) or "access denied" in str(e).lower():
                self.logger.error("Authentication failed. Please check your GitHub token.")
            elif "rejected" in str(e).lower():
                self.logger.error("Push rejected. You may need to pull changes first.")
            else:
                self.logger.error(f"Git error during push: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to push changes: {e}")
            return False
