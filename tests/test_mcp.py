"""
Unit tests for MCP (Master Control Program) tool.
Tests all major functionality with mocking to avoid external dependencies.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json

from mcp.config import MCPConfig
from mcp.git_ops import GitOperations
from mcp.file_ops import FileOperations
from mcp.logger import get_logger


class TestMCPConfig:
    """Test cases for MCPConfig class."""
    
    def test_init_config_new_file(self):
        """Test initializing configuration with new file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = MCPConfig()
            config.config_dir = Path(temp_dir)
            config.config_file = config.config_dir / 'config.json'
            
            with patch('builtins.input', side_effect=['test_token', 'main']):
                result = config.init_config()
                
            assert result is True
            assert config.config_file.exists()
            
            with open(config.config_file, 'r') as f:
                saved_config = json.load(f)
                assert saved_config['github_token'] == 'test_token'
                assert saved_config['default_branch'] == 'main'
    
    @patch.dict('os.environ', {}, clear=True)
    @patch('pathlib.Path.home')
    @patch('mcp.config.load_dotenv')
    def test_load_config_from_file(self, mock_load_dotenv, mock_home):
        """Test loading configuration from file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_home.return_value = Path(temp_dir)
            config = MCPConfig()

            # Create test config file
            test_config = {'github_token': 'file_token', 'default_branch': 'develop'}
            with open(config.config_file, 'w') as f:
                json.dump(test_config, f)

            loaded_config = config.load_config()
            assert loaded_config['github_token'] == 'file_token'
            assert loaded_config['default_branch'] == 'develop'
    
    @patch.dict('os.environ', {'GITHUB_TOKEN': 'env_token'})
    def test_load_config_from_env(self):
        """Test loading configuration from environment variables."""
        config = MCPConfig()
        loaded_config = config.load_config()
        assert loaded_config['github_token'] == 'env_token'
    
    def test_get_github_token_success(self):
        """Test getting GitHub token successfully."""
        with patch.object(MCPConfig, 'load_config', return_value={'github_token': 'test_token'}):
            config = MCPConfig()
            token = config.get_github_token()
            assert token == 'test_token'
    
    def test_get_github_token_missing(self):
        """Test getting GitHub token when missing."""
        with patch.object(MCPConfig, 'load_config', return_value={'github_token': ''}):
            config = MCPConfig()
            token = config.get_github_token()
            assert token is None


class TestGitOperations:
    """Test cases for GitOperations class."""
    
    def test_is_valid_repo_url_valid(self):
        """Test valid repository URL validation."""
        git_ops = GitOperations()
        
        valid_urls = [
            'https://github.com/user/repo.git',
            'https://github.com/user/repo',
            'https://github.com/user-name/repo-name.git',
            'https://github.com/user_name/repo_name'
        ]
        
        for url in valid_urls:
            assert git_ops.is_valid_repo_url(url) is True
    
    def test_is_valid_repo_url_invalid(self):
        """Test invalid repository URL validation."""
        git_ops = GitOperations()
        
        invalid_urls = [
            'https://gitlab.com/user/repo.git',
            'https://github.com/user',
            'https://github.com/',
            'not_a_url',
            'https://github.com/user/repo with spaces'
        ]
        
        for url in invalid_urls:
            assert git_ops.is_valid_repo_url(url) is False
    
    @patch('mcp.git_ops.Repo')
    def test_is_git_repository_valid(self, mock_repo):
        """Test valid Git repository detection."""
        mock_repo.return_value = Mock()
        git_ops = GitOperations()
        
        result = git_ops.is_git_repository('/path/to/repo')
        assert result is True
    
    @patch('mcp.git_ops.Repo')
    def test_is_git_repository_invalid(self, mock_repo):
        """Test invalid Git repository detection."""
        from git import InvalidGitRepositoryError
        mock_repo.side_effect = InvalidGitRepositoryError()
        git_ops = GitOperations()
        
        result = git_ops.is_git_repository('/path/to/invalid')
        assert result is False
    
    @patch('mcp.git_ops.Repo.clone_from')
    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.exists')
    def test_clone_repository_success(self, mock_exists, mock_mkdir, mock_clone):
        """Test successful repository cloning."""
        mock_exists.return_value = False
        mock_clone.return_value = Mock()
        
        git_ops = GitOperations()
        result = git_ops.clone_repository(
            'https://github.com/user/repo.git',
            '/path/to/local'
        )
        
        assert result is True
        mock_clone.assert_called_once()
    
    def test_clone_repository_invalid_url(self):
        """Test cloning with invalid URL."""
        git_ops = GitOperations()
        result = git_ops.clone_repository('invalid_url', '/path/to/local')
        assert result is False


class TestFileOperations:
    """Test cases for FileOperations class."""
    
    def test_is_valid_filename_valid(self):
        """Test valid filename validation."""
        file_ops = FileOperations()
        
        valid_names = [
            'file.txt',
            'my-file.py',
            'file_name.js',
            'File123.html',
            'a.b.c.txt'
        ]
        
        for name in valid_names:
            assert file_ops.is_valid_filename(name) is True
    
    def test_is_valid_filename_invalid(self):
        """Test invalid filename validation."""
        file_ops = FileOperations()
        
        invalid_names = [
            'file<name>.txt',
            'file|name.txt',
            'CON.txt',
            'PRN.py',
            '',
            '   ',
            'a' * 300  # Too long
        ]
        
        for name in invalid_names:
            assert file_ops.is_valid_filename(name) is False
    
    def test_is_valid_path_valid(self):
        """Test valid path validation."""
        file_ops = FileOperations()
        
        valid_paths = [
            'src/components',
            'tests/unit',
            'docs/api/v1',
            'simple_file.txt'
        ]
        
        for path in valid_paths:
            assert file_ops.is_valid_path(path) is True
    
    def test_is_valid_path_invalid(self):
        """Test invalid path validation."""
        file_ops = FileOperations()
        
        invalid_paths = [
            '../../../etc/passwd',
            'src/../../../etc',
            'path/with/../traversal'
        ]
        
        for path in invalid_paths:
            assert file_ops.is_valid_path(path) is False
    
    def test_create_directory_success(self):
        """Test successful directory creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_ops = FileOperations()
            new_dir = Path(temp_dir) / 'new_directory'
            
            result = file_ops.create_directory(str(new_dir))
            
            assert result is True
            assert new_dir.exists()
            assert new_dir.is_dir()
    
    def test_create_file_success(self):
        """Test successful file creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_ops = FileOperations()
            new_file = Path(temp_dir) / 'test_file.txt'
            
            result = file_ops.create_file(str(new_file))
            
            assert result is True
            assert new_file.exists()
            assert new_file.is_file()
    
    def test_add_file_to_section_success(self):
        """Test successful file addition to section."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_ops = FileOperations()
            
            result = file_ops.add_file_to_section(
                temp_dir,
                'src/components',
                'Button.js'
            )
            
            assert result is True
            
            expected_file = Path(temp_dir) / 'src' / 'components' / 'Button.js'
            assert expected_file.exists()
            assert expected_file.is_file()


class TestLogger:
    """Test cases for logger functionality."""
    
    def test_get_logger_creation(self):
        """Test logger creation."""
        logger = get_logger(verbose=True)
        assert logger is not None
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'error')
        assert hasattr(logger, 'debug')
        assert hasattr(logger, 'warning')


if __name__ == '__main__':
    pytest.main([__file__])
