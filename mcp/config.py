"""
Configuration management module for MCP tool.
Handles GitHub tokens, configuration files, and initialization.
"""

import json
import os
from pathlib import Path
from dotenv import load_dotenv
from .logger import get_logger


class MCPConfig:
    """Configuration manager for MCP tool."""
    
    def __init__(self, verbose=False):
        """
        Initialize configuration manager.
        
        Args:
            verbose (bool): Enable verbose logging
        """
        self.logger = get_logger(verbose=verbose)
        self.config_dir = Path.home() / '.mcp'
        self.config_file = self.config_dir / 'config.json'
        self.default_config = {
            'github_token': '',
            'default_branch': 'main',
            'log_level': 'INFO'
        }
        
        # Load environment variables
        load_dotenv()
        
        # Ensure config directory exists
        self.config_dir.mkdir(exist_ok=True)
    
    def init_config(self):
        """
        Initialize configuration file with default values.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if self.config_file.exists():
                response = input(f"Configuration file already exists at {self.config_file}. Overwrite? (y/N): ")
                if response.lower() != 'y':
                    self.logger.info("Configuration initialization cancelled.")
                    return False
            
            # Get GitHub token from user
            github_token = input("Enter your GitHub personal access token (or press Enter to skip): ").strip()
            if github_token:
                self.default_config['github_token'] = github_token
            
            # Get default branch
            default_branch = input("Enter default branch name (default: main): ").strip()
            if default_branch:
                self.default_config['default_branch'] = default_branch
            
            # Save configuration
            with open(self.config_file, 'w') as f:
                json.dump(self.default_config, f, indent=2)
            
            self.logger.info(f"Configuration initialized at {self.config_file}")
            
            if not github_token:
                self.logger.warning("No GitHub token provided. You can set it later using the GITHUB_TOKEN environment variable.")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize configuration: {e}")
            return False
    
    def load_config(self):
        """
        Load configuration from file and environment variables.
        
        Returns:
            dict: Configuration dictionary
        """
        config = self.default_config.copy()
        
        # Load from config file if it exists
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    file_config = json.load(f)
                    config.update(file_config)
                self.logger.debug(f"Loaded configuration from {self.config_file}")
            except Exception as e:
                self.logger.warning(f"Failed to load config file: {e}")
        
        # Override with environment variables
        github_token = os.getenv('GITHUB_TOKEN')
        if github_token:
            config['github_token'] = github_token
            self.logger.debug("Using GitHub token from environment variable")
        
        return config
    
    def get_github_token(self):
        """
        Get GitHub token from configuration or environment.
        
        Returns:
            str: GitHub token or None if not found
        """
        config = self.load_config()
        token = config.get('github_token')
        
        if not token:
            self.logger.error("GitHub token not found. Please run 'mcp init' or set GITHUB_TOKEN environment variable.")
            return None
        
        return token
    
    def get_default_branch(self):
        """
        Get default branch from configuration.
        
        Returns:
            str: Default branch name
        """
        config = self.load_config()
        return config.get('default_branch', 'main')
