#!/usr/bin/env python3
"""
MCP Server Entry Point
Start the MCP web server for GitHub repository management
"""

import sys
import argparse
from mcp.server import start_server

def main():
    """Main entry point for MCP server"""
    parser = argparse.ArgumentParser(
        description="MCP Server - GitHub Repository Management Web Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python mcp_server.py                          # Start server with default settings
  python mcp_server.py --host 0.0.0.0 --port 8080  # Start on all interfaces, port 8080
  python mcp_server.py --reload                 # Start with auto-reload for development
  
Environment Variables:
  MCP_SERVER_HOST     - Server host (default: 127.0.0.1)
  MCP_SERVER_PORT     - Server port (default: 8000)
  MCP_API_KEY         - API key for authentication (default: mcp-default-key)
  MCP_ENABLE_CORS     - Enable CORS (default: true)
  MCP_LOG_LEVEL       - Log level (default: INFO)
  GITHUB_TOKEN        - GitHub personal access token (required)
        """
    )
    
    parser.add_argument(
        "--host",
        default=None,
        help="Host to bind the server to (default: 127.0.0.1)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port to bind the server to (default: 8000)"
    )
    
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )
    
    args = parser.parse_args()
    
    try:
        start_server(
            host=args.host,
            port=args.port,
            reload=args.reload
        )
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
