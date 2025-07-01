"""
MCP Server - Web server implementation for MCP tool
Provides REST API endpoints and SSE support for GitHub repository management
"""

import asyncio
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from .config import MCPConfig
from .git_ops import GitOperations
from .file_ops import FileOperations
from .logger import get_logger

# Security
security = HTTPBearer()

# Global variables for server state
active_operations: Dict[str, Dict] = {}
logger = get_logger()

class ServerConfig:
    """Server configuration settings"""
    def __init__(self):
        self.host = os.getenv("MCP_SERVER_HOST", "127.0.0.1")
        self.port = int(os.getenv("MCP_SERVER_PORT", "8000"))
        self.api_key = os.getenv("MCP_API_KEY", "mcp-default-key")
        self.enable_cors = os.getenv("MCP_ENABLE_CORS", "true").lower() == "true"
        self.log_level = os.getenv("MCP_LOG_LEVEL", "INFO")

server_config = ServerConfig()

# Pydantic models for API requests/responses
class CloneRequest(BaseModel):
    repo_url: str = Field(..., description="GitHub repository URL to clone")
    local_path: str = Field(..., description="Local path where to clone the repository")
    
class PushRequest(BaseModel):
    repo_path: str = Field(..., description="Path to the local repository")
    commit_message: str = Field(..., description="Commit message for the push")
    
class AddFileRequest(BaseModel):
    repo_path: str = Field(..., description="Path to the repository")
    section: str = Field(..., description="Section where to add the file (e.g., 'src/components')")
    filename: str = Field(..., description="Name of the file to create")
    content: Optional[str] = Field("", description="Content of the file")
    
class OperationResponse(BaseModel):
    operation_id: str = Field(..., description="Unique identifier for the operation")
    status: str = Field(..., description="Operation status: pending, running, completed, failed")
    message: str = Field(..., description="Status message")
    created_at: datetime = Field(..., description="Operation creation timestamp")
    completed_at: Optional[datetime] = Field(None, description="Operation completion timestamp")
    result: Optional[Dict[str, Any]] = Field(None, description="Operation result data")
    error: Optional[str] = Field(None, description="Error message if operation failed")

class ServerStatus(BaseModel):
    status: str = Field(..., description="Server status")
    version: str = Field(..., description="MCP version")
    active_operations: int = Field(..., description="Number of active operations")
    uptime: str = Field(..., description="Server uptime")

# Authentication dependency
async def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verify API key authentication"""
    if credentials.credentials != server_config.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return credentials.credentials

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info(f"Starting MCP Server on {server_config.host}:{server_config.port}")
    yield
    logger.info("Shutting down MCP Server")

# Create FastAPI app
app = FastAPI(
    title="MCP Server",
    description="GitHub Repository Management Server",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
if server_config.enable_cors:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Mount static files
static_path = Path(__file__).parent.parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Utility functions
def create_operation(operation_type: str, params: Dict) -> str:
    """Create a new operation and return its ID"""
    operation_id = str(uuid.uuid4())
    active_operations[operation_id] = {
        "id": operation_id,
        "type": operation_type,
        "status": "pending",
        "message": f"Operation {operation_type} created",
        "params": params,
        "created_at": datetime.now(),
        "completed_at": None,
        "result": None,
        "error": None
    }
    return operation_id

def update_operation(operation_id: str, status: str, message: str, result: Optional[Dict] = None, error: Optional[str] = None):
    """Update operation status"""
    if operation_id in active_operations:
        active_operations[operation_id].update({
            "status": status,
            "message": message,
            "result": result,
            "error": error
        })
        if status in ["completed", "failed"]:
            active_operations[operation_id]["completed_at"] = datetime.now()

async def execute_clone_operation(operation_id: str, repo_url: str, local_path: str):
    """Execute clone operation in background"""
    try:
        update_operation(operation_id, "running", "Cloning repository...")
        
        config = MCPConfig()
        git_ops = GitOperations(config)
        
        # Validate repository URL
        if not git_ops.is_valid_repo_url(repo_url):
            raise ValueError(f"Invalid repository URL: {repo_url}")
        
        # Clone repository
        result = git_ops.clone_repository(repo_url, local_path)
        
        update_operation(operation_id, "completed", "Repository cloned successfully", {"path": local_path})
        logger.info(f"Clone operation {operation_id} completed successfully")
        
    except Exception as e:
        error_msg = str(e)
        update_operation(operation_id, "failed", "Clone operation failed", error=error_msg)
        logger.error(f"Clone operation {operation_id} failed: {error_msg}")

async def execute_push_operation(operation_id: str, repo_path: str, commit_message: str):
    """Execute push operation in background"""
    try:
        update_operation(operation_id, "running", "Pushing changes...")
        
        config = MCPConfig()
        git_ops = GitOperations(config)
        
        # Validate repository path
        if not git_ops.is_git_repository(repo_path):
            raise ValueError(f"Not a valid Git repository: {repo_path}")
        
        # Push changes
        result = git_ops.push_changes(repo_path, commit_message)
        
        update_operation(operation_id, "completed", "Changes pushed successfully", {"commit_message": commit_message})
        logger.info(f"Push operation {operation_id} completed successfully")
        
    except Exception as e:
        error_msg = str(e)
        update_operation(operation_id, "failed", "Push operation failed", error=error_msg)
        logger.error(f"Push operation {operation_id} failed: {error_msg}")

async def execute_add_file_operation(operation_id: str, repo_path: str, section: str, filename: str, content: str):
    """Execute add file operation in background"""
    try:
        update_operation(operation_id, "running", "Creating file...")
        
        file_ops = FileOperations()
        
        # Validate inputs
        if not file_ops.is_valid_filename(filename):
            raise ValueError(f"Invalid filename: {filename}")
        
        if not file_ops.is_valid_path(repo_path):
            raise ValueError(f"Invalid repository path: {repo_path}")
        
        # Create file
        result = file_ops.add_file_to_section(repo_path, section, filename, content)
        
        update_operation(operation_id, "completed", "File created successfully", {
            "path": result,
            "section": section,
            "filename": filename
        })
        logger.info(f"Add file operation {operation_id} completed successfully")
        
    except Exception as e:
        error_msg = str(e)
        update_operation(operation_id, "failed", "Add file operation failed", error=error_msg)
        logger.error(f"Add file operation {operation_id} failed: {error_msg}")

# API Routes

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint - serves the web interface"""
    static_path = Path(__file__).parent.parent / "static" / "index.html"
    if static_path.exists():
        with open(static_path, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>MCP Server</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; text-align: center; }
                .container { max-width: 600px; margin: 0 auto; }
                .error { color: #e74c3c; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>MCP Server</h1>
                <p class="error">Web interface not found. Please ensure static files are properly installed.</p>
                <p><a href="/docs">View API Documentation</a></p>
            </div>
        </body>
        </html>
        """

@app.get("/status", response_model=ServerStatus)
async def get_status():
    """Get server status and health information"""
    return ServerStatus(
        status="running",
        version="1.0.0",
        active_operations=len([op for op in active_operations.values() if op["status"] in ["pending", "running"]]),
        uptime="N/A"  # TODO: Implement uptime tracking
    )

@app.post("/api/clone", response_model=OperationResponse)
async def clone_repository(
    request: CloneRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
):
    """Clone a GitHub repository"""
    operation_id = create_operation("clone", {
        "repo_url": request.repo_url,
        "local_path": request.local_path
    })

    # Start background task
    background_tasks.add_task(
        execute_clone_operation,
        operation_id,
        request.repo_url,
        request.local_path
    )

    operation = active_operations[operation_id]
    return OperationResponse(**operation)

@app.post("/api/push", response_model=OperationResponse)
async def push_changes(
    request: PushRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
):
    """Push changes to GitHub repository"""
    operation_id = create_operation("push", {
        "repo_path": request.repo_path,
        "commit_message": request.commit_message
    })

    # Start background task
    background_tasks.add_task(
        execute_push_operation,
        operation_id,
        request.repo_path,
        request.commit_message
    )

    operation = active_operations[operation_id]
    return OperationResponse(**operation)

@app.post("/api/add-file", response_model=OperationResponse)
async def add_file(
    request: AddFileRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
):
    """Add a file to repository section"""
    operation_id = create_operation("add-file", {
        "repo_path": request.repo_path,
        "section": request.section,
        "filename": request.filename,
        "content": request.content
    })

    # Start background task
    background_tasks.add_task(
        execute_add_file_operation,
        operation_id,
        request.repo_path,
        request.section,
        request.filename,
        request.content
    )

    operation = active_operations[operation_id]
    return OperationResponse(**operation)

@app.get("/api/operations/{operation_id}", response_model=OperationResponse)
async def get_operation(operation_id: str, api_key: str = Depends(verify_api_key)):
    """Get status of a specific operation"""
    if operation_id not in active_operations:
        raise HTTPException(status_code=404, detail="Operation not found")

    operation = active_operations[operation_id]
    return OperationResponse(**operation)

@app.get("/api/operations", response_model=List[OperationResponse])
async def list_operations(api_key: str = Depends(verify_api_key)):
    """List all operations"""
    operations = [OperationResponse(**op) for op in active_operations.values()]
    return sorted(operations, key=lambda x: x.created_at, reverse=True)

# Server-Sent Events endpoint
@app.get("/events")
async def stream_events(api_key: str = Depends(verify_api_key)):
    """Stream real-time operation updates via Server-Sent Events"""

    async def event_generator():
        """Generate SSE events for operation updates"""
        last_update = datetime.now()

        # Send initial connection event
        yield f"data: {json.dumps({'type': 'connected', 'message': 'Connected to MCP Server events', 'timestamp': datetime.now().isoformat()})}\n\n"

        while True:
            try:
                # Check for operation updates
                current_time = datetime.now()

                # Send periodic heartbeat
                if (current_time - last_update).seconds >= 30:
                    yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': current_time.isoformat()})}\n\n"
                    last_update = current_time

                # Send operation status updates
                for operation_id, operation in active_operations.items():
                    # Send updates for recently modified operations
                    if operation.get('last_sent_at', datetime.min) < operation.get('updated_at', operation['created_at']):
                        event_data = {
                            'type': 'operation_update',
                            'operation_id': operation_id,
                            'status': operation['status'],
                            'message': operation['message'],
                            'timestamp': current_time.isoformat()
                        }

                        if operation['status'] == 'completed' and operation.get('result'):
                            event_data['result'] = operation['result']
                        elif operation['status'] == 'failed' and operation.get('error'):
                            event_data['error'] = operation['error']

                        yield f"data: {json.dumps(event_data)}\n\n"
                        operation['last_sent_at'] = current_time

                # Wait before next check
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Error in event stream: {e}")
                yield f"data: {json.dumps({'type': 'error', 'message': str(e), 'timestamp': datetime.now().isoformat()})}\n\n"
                break

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )

# Server startup function
def start_server(host: str = None, port: int = None, reload: bool = False):
    """Start the MCP server"""
    host = host or server_config.host
    port = port or server_config.port

    logger.info(f"Starting MCP Server on {host}:{port}")
    logger.info(f"API Key: {server_config.api_key}")
    logger.info(f"CORS Enabled: {server_config.enable_cors}")

    uvicorn.run(
        "mcp.server:app",
        host=host,
        port=port,
        reload=reload,
        log_level=server_config.log_level.lower()
    )

if __name__ == "__main__":
    start_server()
