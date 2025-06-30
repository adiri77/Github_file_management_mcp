"""
File operations module for MCP tool.
Provides file creation and directory management functionality.
"""

import os
import re
from pathlib import Path
from .logger import get_logger


class FileOperations:
    """File operations manager for MCP tool."""
    
    def __init__(self, verbose=False):
        """
        Initialize file operations manager.
        
        Args:
            verbose (bool): Enable verbose logging
        """
        self.logger = get_logger(verbose=verbose)
    
    def is_valid_filename(self, filename):
        """
        Check if filename is valid for cross-platform compatibility.
        
        Args:
            filename (str): Filename to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        # Check for invalid characters
        invalid_chars = r'[<>:"/\\|?*]'
        if re.search(invalid_chars, filename):
            return False
        
        # Check for reserved names on Windows
        reserved_names = {
            'CON', 'PRN', 'AUX', 'NUL',
            'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
            'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        }
        
        name_without_ext = filename.split('.')[0].upper()
        if name_without_ext in reserved_names:
            return False
        
        # Check length (255 is common filesystem limit)
        if len(filename) > 255:
            return False
        
        # Check for empty or whitespace-only names
        if not filename.strip():
            return False
        
        return True
    
    def is_valid_path(self, path):
        """
        Check if path is valid and safe.
        
        Args:
            path (str): Path to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            # Convert to Path object for validation
            path_obj = Path(path)
            
            # Check for path traversal attempts
            if '..' in path_obj.parts:
                return False
            
            # Check each part of the path
            for part in path_obj.parts:
                if not self.is_valid_filename(part):
                    return False
            
            return True
            
        except Exception:
            return False
    
    def create_directory(self, directory_path, dry_run=False):
        """
        Create directory if it doesn't exist.
        
        Args:
            directory_path (str): Path to directory
            dry_run (bool): If True, simulate operation without making changes
            
        Returns:
            bool: True if successful or already exists, False otherwise
        """
        try:
            path_obj = Path(directory_path)
            
            if path_obj.exists():
                if path_obj.is_dir():
                    self.logger.debug(f"Directory already exists: {directory_path}")
                    return True
                else:
                    self.logger.error(f"Path exists but is not a directory: {directory_path}")
                    return False
            
            if dry_run:
                self.logger.info(f"[DRY RUN] Would create directory: {directory_path}")
                return True
            
            path_obj.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Created directory: {directory_path}")
            return True
            
        except PermissionError:
            self.logger.error(f"Permission denied creating directory: {directory_path}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to create directory {directory_path}: {e}")
            return False
    
    def create_file(self, file_path, dry_run=False, overwrite=False):
        """
        Create an empty file (equivalent to touch command).
        
        Args:
            file_path (str): Path to file
            dry_run (bool): If True, simulate operation without making changes
            overwrite (bool): If True, overwrite existing file without prompting
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            path_obj = Path(file_path)
            
            # Validate filename
            if not self.is_valid_filename(path_obj.name):
                self.logger.error(f"Invalid filename: {path_obj.name}")
                return False
            
            # Check if file already exists
            if path_obj.exists():
                if not overwrite:
                    response = input(f"File {file_path} already exists. Overwrite? (y/N): ")
                    if response.lower() != 'y':
                        self.logger.info("File creation cancelled.")
                        return False
                
                if dry_run:
                    self.logger.info(f"[DRY RUN] Would overwrite file: {file_path}")
                    return True
            
            # Create parent directories if they don't exist
            if not self.create_directory(path_obj.parent, dry_run=dry_run):
                return False
            
            if dry_run:
                self.logger.info(f"[DRY RUN] Would create file: {file_path}")
                return True
            
            # Create the file
            path_obj.touch()
            self.logger.info(f"Created file: {file_path}")
            return True
            
        except PermissionError:
            self.logger.error(f"Permission denied creating file: {file_path}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to create file {file_path}: {e}")
            return False
    
    def add_file_to_section(self, repo_path, section, filename, dry_run=False, overwrite=False):
        """
        Add a file to a specific section (subdirectory) of a repository.
        
        Args:
            repo_path (str): Path to repository
            section (str): Section (subdirectory) path relative to repo
            filename (str): Name of file to create
            dry_run (bool): If True, simulate operation without making changes
            overwrite (bool): If True, overwrite existing file without prompting
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            repo_path_obj = Path(repo_path)
            
            # Validate repository path
            if not repo_path_obj.exists():
                self.logger.error(f"Repository path does not exist: {repo_path}")
                return False
            
            if not repo_path_obj.is_dir():
                self.logger.error(f"Repository path is not a directory: {repo_path}")
                return False
            
            # Validate section path
            if not self.is_valid_path(section):
                self.logger.error(f"Invalid section path: {section}")
                return False
            
            # Construct full path
            section_path = repo_path_obj / section
            file_path = section_path / filename
            
            # Create the file
            return self.create_file(str(file_path), dry_run=dry_run, overwrite=overwrite)
            
        except Exception as e:
            self.logger.error(f"Failed to add file to section: {e}")
            return False
