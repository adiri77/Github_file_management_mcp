"""
MCP (Master Control Program) - GitHub repository management tool.

A Python-based command-line tool that provides functionality to:
- Clone GitHub repositories
- Push changes to GitHub
- Create files in specific repository sections
"""

__version__ = "1.0.0"
__author__ = "MCP Development Team"
__email__ = "mcp@example.com"
__description__ = "Master Control Program for GitHub repository management"

# Import main classes for easy access
from .config import MCPConfig
from .git_ops import GitOperations
from .file_ops import FileOperations
from .logger import get_logger

__all__ = [
    'MCPConfig',
    'GitOperations', 
    'FileOperations',
    'get_logger'
]
