"""
Claude Orchestration MCP Server - Implementation Starter

This is a starter template for implementing the Claude Orchestration MCP Server
using the Gradio MCP library for the hackathon.

Requirements:
- pip install gradio-mcp httpx python-dotenv
"""

import os
import asyncio
from typing import Dict, List, Optional, Any
import httpx
from gradio_mcp import MCPServer
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

class ClaudeOrchestrationMCP:
    """MCP Server for orchestrating Claude Code sessions"""
    
    def __init__(self):
        self.api_url = os.getenv("CLAUDE_HUB_API_URL", "http://localhost:3002/api/webhooks/claude")
        self.auth_token = os.getenv("CLAUDE_WEBHOOK_SECRET", "")
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def _make_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make authenticated request to Claude Hub API"""
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = await self.client.post(
                self.api_url,
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            return {
                "error": f"API request failed: {str(e)}",
                "success": False
            }
    
    async def create_session(
        self,
        session_type: str,
        repository: str,
        requirements: str,
        context: Optional[str] = None,
        dependencies: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a new Claude Code session for a specific subtask"""
        
        payload = {
            "type": "session.create",
            "session": {
                "type": session_type,
                "project": {
                    "repository": repository,
                    "requirements": requirements,
                    "context": context or ""
                },
                "dependencies": dependencies or []
            }
        }
        
        result = await self._make_request(payload)
        
        if result.get("success"):
            session = result.get("data", {}).get("session", {})
            return {
                "session_id": session.get("id"),
                "status": session.get("status"),
                "type": session.get("type"),
                "container_id": session.get("containerId")
            }
        else:
            raise Exception(result.get("error", "Failed to create session"))
    
    async def start_session(self, session_id: str) -> Dict[str, Any]:
        """Start a previously created session"""
        
        payload = {
            "type": "session.start",
            "sessionId": session_id
        }
        
        result = await self._make_request(payload)
        
        if result.get("success"):
            data = result.get("data", {})
            return {
                "started": data.get("started", False),
                "status": data.get("status"),
                "message": data.get("message", "Session start requested")
            }
        else:
            raise Exception(result.get("error", "Failed to start session"))
    
    async def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get the current status of a session"""
        
        payload = {
            "type": "session.get",
            "sessionId": session_id
        }
        
        result = await self._make_request(payload)
        
        if result.get("success"):
            session = result.get("data", {}).get("session", {})
            return {
                "session_id": session.get("id"),
                "status": session.get("status"),
                "type": session.get("type"),
                "progress": session.get("progress", ""),
                "created_at": session.get("createdAt"),
                "started_at": session.get("startedAt"),
                "container_id": session.get("containerId")
            }
        else:
            raise Exception(result.get("error", "Failed to get session status"))
    
    async def get_session_output(self, session_id: str) -> Dict[str, Any]:
        """Get the output from a completed session"""
        
        payload = {
            "type": "session.output",
            "sessionId": session_id
        }
        
        result = await self._make_request(payload)
        
        if result.get("success"):
            data = result.get("data", {})
            return {
                "session_id": session_id,
                "status": data.get("status"),
                "output": data.get("output", {})
            }
        else:
            raise Exception(result.get("error", "Failed to get session output"))
    
    async def list_sessions(
        self, 
        orchestration_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """List all sessions, optionally filtered"""
        
        payload = {
            "type": "session.list"
        }
        
        if orchestration_id:
            payload["orchestrationId"] = orchestration_id
            
        result = await self._make_request(payload)
        
        if result.get("success"):
            sessions = result.get("data", {}).get("sessions", [])
            
            # Filter by status if requested
            if status and status != "all":
                sessions = [s for s in sessions if s.get("status") == status]
            
            return {
                "sessions": sessions,
                "total": len(sessions)
            }
        else:
            raise Exception(result.get("error", "Failed to list sessions"))
    
    async def wait_for_session(
        self,
        session_id: str,
        timeout_seconds: int = 3600,
        poll_interval_seconds: int = 10
    ) -> Dict[str, Any]:
        """Wait for a session to complete with polling"""
        
        start_time = asyncio.get_event_loop().time()
        
        while True:
            # Check if timeout exceeded
            if asyncio.get_event_loop().time() - start_time > timeout_seconds:
                raise TimeoutError(f"Session {session_id} did not complete within {timeout_seconds} seconds")
            
            # Get session status
            status = await self.get_session_status(session_id)
            
            if status["status"] in ["completed", "failed"]:
                # Get final output
                if status["status"] == "completed":
                    output = await self.get_session_output(session_id)
                    return {
                        "session_id": session_id,
                        "status": status["status"],
                        "duration_seconds": int(asyncio.get_event_loop().time() - start_time),
                        "output": output.get("output", {})
                    }
                else:
                    return {
                        "session_id": session_id,
                        "status": "failed",
                        "error": "Session failed",
                        "duration_seconds": int(asyncio.get_event_loop().time() - start_time)
                    }
            
            # Wait before next poll
            await asyncio.sleep(poll_interval_seconds)


# Initialize the orchestration client
orchestration = ClaudeOrchestrationMCP()

# Create the MCP server
mcp_server = MCPServer(
    name="claude-orchestration",
    description="Orchestrate multiple Claude Code sessions for complex software projects"
)

# Register all tools
mcp_server.register_tool(
    name="create_session",
    function=orchestration.create_session,
    description="Create a new Claude Code session for a specific subtask",
    parameters={
        "type": "object",
        "properties": {
            "session_type": {
                "type": "string",
                "enum": ["implementation", "analysis", "testing", "review", "documentation"],
                "description": "Type of session based on the task"
            },
            "repository": {
                "type": "string",
                "description": "Repository in format 'owner/repo'"
            },
            "requirements": {
                "type": "string",
                "description": "Detailed requirements for this specific session"
            },
            "context": {
                "type": "string",
                "description": "Additional context about the overall project"
            },
            "dependencies": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Session IDs that must complete first"
            }
        },
        "required": ["session_type", "repository", "requirements"]
    }
)

mcp_server.register_tool(
    name="start_session",
    function=orchestration.start_session,
    description="Start a previously created session or queue it if dependencies aren't met",
    parameters={
        "type": "object",
        "properties": {
            "session_id": {
                "type": "string",
                "description": "The ID of the session to start"
            }
        },
        "required": ["session_id"]
    }
)

mcp_server.register_tool(
    name="get_session_status",
    function=orchestration.get_session_status,
    description="Get the current status and details of a session",
    parameters={
        "type": "object",
        "properties": {
            "session_id": {
                "type": "string",
                "description": "The ID of the session to check"
            }
        },
        "required": ["session_id"]
    }
)

mcp_server.register_tool(
    name="get_session_output",
    function=orchestration.get_session_output,
    description="Get the output and results from a completed session",
    parameters={
        "type": "object",
        "properties": {
            "session_id": {
                "type": "string",
                "description": "The ID of the completed session"
            }
        },
        "required": ["session_id"]
    }
)

mcp_server.register_tool(
    name="list_sessions",
    function=orchestration.list_sessions,
    description="List all sessions, optionally filtered by orchestration ID or status",
    parameters={
        "type": "object",
        "properties": {
            "orchestration_id": {
                "type": "string",
                "description": "Optional orchestration ID to filter sessions"
            },
            "status": {
                "type": "string",
                "enum": ["pending", "running", "completed", "failed", "all"],
                "description": "Filter by session status"
            }
        }
    }
)

mcp_server.register_tool(
    name="wait_for_session",
    function=orchestration.wait_for_session,
    description="Wait for a session to complete with polling",
    parameters={
        "type": "object",
        "properties": {
            "session_id": {
                "type": "string",
                "description": "The ID of the session to wait for"
            },
            "timeout_seconds": {
                "type": "integer",
                "description": "Maximum seconds to wait (default: 3600)"
            },
            "poll_interval_seconds": {
                "type": "integer",
                "description": "Seconds between status checks (default: 10)"
            }
        },
        "required": ["session_id"]
    }
)

# Example Gradio interface (optional - for testing)
if __name__ == "__main__":
    # You can add a Gradio UI here for testing the MCP server
    # or run it as a standalone service
    print("Claude Orchestration MCP Server initialized")
    print(f"API URL: {orchestration.api_url}")
    print("Available tools:", [tool.name for tool in mcp_server.tools])