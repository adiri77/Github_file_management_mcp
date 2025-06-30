"""
Logging module for MCP tool.
Provides console and file logging with configurable verbosity levels.
"""

import logging
import os
from pathlib import Path


class MCPLogger:
    """Logger class for MCP tool with console and file output."""
    
    def __init__(self, verbose=False, log_file="mcp.log"):
        """
        Initialize the logger.
        
        Args:
            verbose (bool): Enable verbose (DEBUG) logging
            log_file (str): Path to log file
        """
        self.verbose = verbose
        self.log_file = log_file
        self.logger = logging.getLogger('mcp')
        self.logger.setLevel(logging.DEBUG if verbose else logging.INFO)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Create formatters
        console_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
        except Exception as e:
            self.logger.warning(f"Could not create log file {log_file}: {e}")
    
    def info(self, message):
        """Log info message."""
        self.logger.info(message)
    
    def error(self, message):
        """Log error message."""
        self.logger.error(message)
    
    def debug(self, message):
        """Log debug message."""
        self.logger.debug(message)
    
    def warning(self, message):
        """Log warning message."""
        self.logger.warning(message)


def get_logger(verbose=False, log_file="mcp.log"):
    """
    Get a configured logger instance.
    
    Args:
        verbose (bool): Enable verbose logging
        log_file (str): Path to log file
        
    Returns:
        MCPLogger: Configured logger instance
    """
    return MCPLogger(verbose=verbose, log_file=log_file)
