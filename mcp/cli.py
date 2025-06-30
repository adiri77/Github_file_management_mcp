#!/usr/bin/env python3
"""
MCP (Master Control Program) - Command Line Interface

This module provides the main CLI entry point for the MCP tool.
"""

import argparse
import sys
from pathlib import Path

from .config import MCPConfig
from .git_ops import GitOperations
from .file_ops import FileOperations
from .logger import get_logger


def create_parser():
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog='mcp',
        description='MCP (Master Control Program) - GitHub repository management tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  mcp init                                    # Initialize configuration
  mcp clone https://github.com/user/repo.git ./my-repo
  mcp add-file ./my-repo src/utils helper.py
  mcp push ./my-repo "Added helper.py to utils"
        """
    )
    
    # Global options
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate operations without making changes'
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Init command
    init_parser = subparsers.add_parser(
        'init',
        help='Initialize MCP configuration'
    )
    
    # Clone command
    clone_parser = subparsers.add_parser(
        'clone',
        help='Clone a GitHub repository'
    )
    clone_parser.add_argument(
        'repo_url',
        help='GitHub repository URL (e.g., https://github.com/user/repo.git)'
    )
    clone_parser.add_argument(
        'local_path',
        help='Local path to clone the repository to'
    )
    
    # Push command
    push_parser = subparsers.add_parser(
        'push',
        help='Push changes to GitHub'
    )
    push_parser.add_argument(
        'local_path',
        help='Path to local Git repository'
    )
    push_parser.add_argument(
        'commit_message',
        help='Commit message for the changes'
    )
    
    # Add-file command
    add_file_parser = subparsers.add_parser(
        'add-file',
        help='Create a file in a specific repository section'
    )
    add_file_parser.add_argument(
        'local_path',
        help='Path to local Git repository'
    )
    add_file_parser.add_argument(
        'section',
        help='Section (subdirectory) path relative to repository root'
    )
    add_file_parser.add_argument(
        'filename',
        help='Name of the file to create'
    )
    add_file_parser.add_argument(
        '--overwrite',
        action='store_true',
        help='Overwrite existing file without prompting'
    )
    
    return parser


def handle_init(args, config, logger):
    """Handle the init command."""
    logger.info("Initializing MCP configuration...")
    
    if config.init_config():
        logger.info("Configuration initialized successfully.")
        return 0
    else:
        logger.error("Failed to initialize configuration.")
        return 1


def handle_clone(args, git_ops, logger):
    """Handle the clone command."""
    logger.info(f"Cloning repository {args.repo_url} to {args.local_path}...")
    
    if git_ops.clone_repository(args.repo_url, args.local_path, dry_run=args.dry_run):
        if not args.dry_run:
            logger.info("Repository cloned successfully.")
        return 0
    else:
        logger.error("Failed to clone repository.")
        return 1


def handle_push(args, git_ops, logger):
    """Handle the push command."""
    logger.info(f"Pushing changes from {args.local_path}...")
    
    if git_ops.push_changes(args.local_path, args.commit_message, dry_run=args.dry_run):
        if not args.dry_run:
            logger.info("Changes pushed successfully.")
        return 0
    else:
        logger.error("Failed to push changes.")
        return 1


def handle_add_file(args, file_ops, logger):
    """Handle the add-file command."""
    logger.info(f"Creating file {args.filename} in section {args.section}...")
    
    if file_ops.add_file_to_section(
        args.local_path, 
        args.section, 
        args.filename, 
        dry_run=args.dry_run,
        overwrite=args.overwrite
    ):
        if not args.dry_run:
            logger.info("File created successfully.")
        return 0
    else:
        logger.error("Failed to create file.")
        return 1


def main():
    """Main entry point for the MCP tool."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Show help if no command provided
    if not args.command:
        parser.print_help()
        return 0
    
    # Initialize logger
    logger = get_logger(verbose=args.verbose)
    
    # Initialize components
    config = MCPConfig(verbose=args.verbose)
    git_ops = GitOperations(verbose=args.verbose)
    file_ops = FileOperations(verbose=args.verbose)
    
    try:
        # Handle commands
        if args.command == 'init':
            return handle_init(args, config, logger)
        elif args.command == 'clone':
            return handle_clone(args, git_ops, logger)
        elif args.command == 'push':
            return handle_push(args, git_ops, logger)
        elif args.command == 'add-file':
            return handle_add_file(args, file_ops, logger)
        else:
            logger.error(f"Unknown command: {args.command}")
            return 2
    
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user.")
        return 130
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
