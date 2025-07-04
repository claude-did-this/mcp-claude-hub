"""
Claude Orchestration MCP Server - Fixed Event Loop Handling

This server provides tools for orchestrating multiple Claude Code sessions
to work on complex projects in parallel.
"""

import os
import asyncio
from typing import Dict, List, Optional, Any
import httpx
from dotenv import load_dotenv
import json
import gradio as gr
import concurrent.futures
import nest_asyncio

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Load environment variables
load_dotenv()


class ClaudeOrchestrationMCP:
    """MCP Server for orchestrating Claude Code sessions"""
    
    def __init__(self):
        self.api_url = os.getenv("CLAUDE_HUB_API_URL", "http://localhost:3002/api/webhooks/claude")
        self.auth_token = os.getenv("CLAUDE_WEBHOOK_SECRET", "")
        self.client = None
        
    async def _ensure_client(self):
        """Ensure httpx client is created"""
        if self.client is None:
            self.client = httpx.AsyncClient(timeout=30.0)
    
    async def _make_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make authenticated request to Claude Hub API"""
        await self._ensure_client()
        
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
            data = response.json()
            
            # Validate response is a dictionary
            if not isinstance(data, dict):
                return {
                    "message": "Webhook processing failed",
                    "event": payload.get("type", "unknown"),
                    "handlerCount": 0,
                    "results": [{
                        "success": False,
                        "error": f"Invalid response format: expected dictionary, got {type(data).__name__}"
                    }]
                }
            
            # If the response has a standard API format, convert to webhook format
            if "success" in data and "results" not in data:
                return {
                    "message": "Webhook processed" if data.get("success") else "Webhook processing failed",
                    "event": payload.get("type", "unknown"),
                    "handlerCount": 1 if data.get("success") else 0,
                    "results": [{
                        "success": bool(data.get("success")),
                        "message": data.get("message", ""),
                        "data": data.get("data", {}),
                        "error": data.get("error")
                    }]
                }
            else:
                return data
        except httpx.HTTPError as e:
            # Return in webhook handler format
            return {
                "message": "Webhook processing failed",
                "event": payload.get("type", "unknown"),
                "handlerCount": 0,
                "results": [{
                    "success": False,
                    "error": f"API request failed: {str(e)}"
                }]
            }
    
    async def create_session(
        self,
        session_type: str,
        repository: str,
        requirements: str,
        context: Optional[str] = None,
        branch: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
        auto_start: bool = True,
        timeout_minutes: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create a new Claude Code session for a specific subtask
        
        Args:
            session_type: Type of session - implementation, analysis, testing, review, or coordination
            repository: GitHub repository in "owner/repo" format
            requirements: Clear description of what Claude should do
            context: Additional context about the codebase or requirements
            branch: Target branch name (defaults to main/master)
            dependencies: Array of session IDs that must complete before this session starts
            auto_start: Whether to automatically start the session when dependencies are met (default: True)
            timeout_minutes: Maximum runtime in minutes before session is terminated
        """
        
        # Validate session type
        valid_session_types = {"implementation", "analysis", "testing", "review", "coordination"}
        if session_type not in valid_session_types:
            return {
                "message": "Webhook processing failed",
                "event": "session.create",
                "handlerCount": 0,
                "results": [{
                    "success": False,
                    "error": f"Invalid session type: {session_type}. Must be one of: {', '.join(sorted(valid_session_types))}"
                }]
            }
        
        # Validate repository format
        if not repository or "/" not in repository:
            return {
                "message": "Webhook processing failed",
                "event": "session.create",
                "handlerCount": 0,
                "results": [{
                    "success": False,
                    "error": "Invalid repository format. Must be in 'owner/repo' format"
                }]
            }
        
        # Validate repository has exactly one slash
        parts = repository.split("/")
        if len(parts) != 2 or not parts[0] or not parts[1]:
            return {
                "message": "Webhook processing failed",
                "event": "session.create",
                "handlerCount": 0,
                "results": [{
                    "success": False,
                    "error": "Invalid repository format. Must be in 'owner/repo' format with non-empty owner and repo names"
                }]
            }
        
        # Validate requirements is not empty
        if not requirements or not requirements.strip():
            return {
                "message": "Webhook processing failed",
                "event": "session.create",
                "handlerCount": 0,
                "results": [{
                    "success": False,
                    "error": "Requirements cannot be empty"
                }]
            }
        
        # Build project data
        project_data = {
            "repository": repository,
            "requirements": requirements
        }
        
        if context:
            project_data["context"] = context
        
        if branch:
            project_data["branch"] = branch
        
        # Filter out invalid dependencies
        valid_deps = []
        if dependencies:
            for dep in dependencies:
                # Skip empty strings and 'None' string
                if dep and dep.lower() != 'none':
                    valid_deps.append(dep)
        
        # Build session options
        options = {
            "autoStart": auto_start
        }
        
        if timeout_minutes:
            options["timeout"] = timeout_minutes * 60  # Convert to seconds
        
        payload = {
            "type": "session.create",
            "session": {
                "type": session_type,
                "project": project_data,
                "dependencies": valid_deps,
                "options": options
            }
        }
        
        result = await self._make_request(payload)
        
        # Extract data from webhook response (v2.0.0 format)
        if "results" in result and isinstance(result.get("results"), list) and len(result.get("results", [])) > 0:
            first_result = result["results"][0]
            if isinstance(first_result, dict) and first_result.get("success"):
                data = first_result.get("data", {})
                # v2.0.0: data is wrapped in data.session
                session_data = data.get("session", data)
                session_id = session_data.get("id") or session_data.get("sessionId")
                
                if session_id:
                    return {
                        "message": "Webhook processed",
                        "event": "session.create",
                        "handlerCount": 1,
                        "results": [{
                            "success": True,
                            "message": "Session created",
                            "data": {
                                "session": {
                                    "id": session_id,
                                    "status": session_data.get("status", "pending"),
                                    "type": session_type,
                                    "autoStart": auto_start
                                }
                            }
                        }]
                    }
                else:
                    # Session ID not found in expected locations
                    return {
                        "message": "Webhook processing failed",
                        "event": "session.create",
                        "handlerCount": 0,
                        "results": [{
                            "success": False,
                            "error": "Session ID not found in API response"
                        }]
                    }
        
        return result  # Return as-is if error or unexpected format
    
    async def start_session(self, session_id: str) -> Dict[str, Any]:
        """Start a previously created session"""
        
        payload = {
            "type": "session.start",
            "sessionId": session_id
        }
        
        result = await self._make_request(payload)
        
        # Extract data from webhook response
        if "results" in result and len(result.get("results", [])) > 0:
            first_result = result["results"][0]
            if first_result.get("success"):
                data = first_result.get("data", {})
                # v2.0.0: data is wrapped in data.session
                session_data = data.get("session", data)
                status = session_data.get("status", "initializing")
                
                return {
                    "message": "Webhook processed",
                    "event": "session.start",
                    "handlerCount": 1,
                    "results": [{
                        "success": True,
                        "message": "Session starting" if status == "initializing" else f"Session {status}",
                        "data": {
                            "session": {
                                "status": status
                            }
                        }
                    }]
                }
        
        return result  # Return as-is if error or unexpected format
    
    async def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get the current status and details of a session
        
        Returns session info including:
            status: pending, initializing, running, completed, failed, cancelled, or queued
            containerId: Docker container ID if running
            claudeSessionId: Internal Claude session ID
            startedAt: ISO timestamp when session started
            completedAt: ISO timestamp when session completed
            error: Error message if failed
        """
        
        payload = {
            "type": "session.get",
            "sessionId": session_id
        }
        
        result = await self._make_request(payload)
        
        # Check if response is in webhook handler format
        if "results" in result and len(result.get("results", [])) > 0:
            first_result = result["results"][0]
            if first_result.get("success"):
                data = first_result.get("data", {})
                # v2.0.0: data is wrapped in data.session
                session = data.get("session", data)
                return {
                    "message": "Webhook processed",
                    "event": "session.get",
                    "handlerCount": 1,
                    "results": [{
                        "success": True,
                        "data": {
                            "session": {
                                "id": session.get("id"),
                                "type": session.get("type"),
                                "status": session.get("status"),
                                "containerId": session.get("containerId"),
                                "claudeSessionId": session.get("claudeSessionId"),
                                "project": session.get("project", {}),
                                "dependencies": session.get("dependencies", []),
                                "startedAt": session.get("startedAt"),
                                "completedAt": session.get("completedAt"),
                                "output": session.get("output"),
                                "error": session.get("error")
                            }
                        }
                    }]
                }
            else:
                return result  # Return error response as-is
        else:
            # Fallback for unexpected response format
            return {
                "message": "Webhook processed",
                "event": "session.get",
                "handlerCount": 1,
                "results": [{
                    "success": False,
                    "error": "Unexpected response format from API"
                }]
            }
    
    async def get_session_output(self, session_id: str) -> Dict[str, Any]:
        """Get the output and artifacts from a completed session
        
        Returns:
            logs: Array of log entries from the session
            artifacts: Array of artifacts (files, commits, PRs, etc.) created
            summary: Brief summary of what was accomplished
            nextSteps: Suggested next steps
        """
        
        payload = {
            "type": "session.output",
            "sessionId": session_id
        }
        
        result = await self._make_request(payload)
        
        # Check if response is in webhook handler format
        if "results" in result and len(result.get("results", [])) > 0:
            first_result = result["results"][0]
            if first_result.get("success"):
                data = first_result.get("data", {})
                # v2.0.0: data may be wrapped
                session_data = data.get("session", data)
                output = session_data.get("output", {})
                return {
                    "message": "Webhook processed",
                    "event": "session.output",
                    "handlerCount": 1,
                    "results": [{
                        "success": True,
                        "data": {
                            "sessionId": session_data.get("id", session_id),
                            "status": session_data.get("status", "completed"),
                            "output": {
                                "logs": output.get("logs", []),
                                "artifacts": output.get("artifacts", []),
                                "summary": output.get("summary", ""),
                                "nextSteps": output.get("nextSteps", [])
                            }
                        }
                    }]
                }
            else:
                return result  # Return error response as-is
        else:
            # Fallback for unexpected response format
            return {
                "message": "Webhook processed",
                "event": "session.output",
                "handlerCount": 1,
                "results": [{
                    "success": False,
                    "error": "Unexpected response format from API"
                }]
            }
    
    async def list_sessions(
        self, 
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """List all sessions, optionally filtered by status
        
        Args:
            status: Filter by status (pending, initializing, running, completed, failed, cancelled, queued)
        """
        
        payload = {
            "type": "session.list"
        }
        
        if status and status != "all":
            payload["status"] = status
            
        result = await self._make_request(payload)
        
        # Check if response is in webhook handler format
        if "results" in result and len(result.get("results", [])) > 0:
            first_result = result["results"][0]
            if first_result.get("success"):
                data = first_result.get("data", {})
                # v2.0.0: data is wrapped in data.sessions
                sessions = data.get("sessions", [])
                
                return {
                    "message": "Webhook processed",
                    "event": "session.list",
                    "handlerCount": 1,
                    "results": [{
                        "success": True,
                        "data": {
                            "sessions": sessions
                        }
                    }]
                }
            else:
                return result  # Return error response as-is
        else:
            # Fallback for unexpected response format
            return {
                "message": "Webhook processed",
                "event": "session.list",
                "handlerCount": 1,
                "results": [{
                    "success": False,
                    "error": "Unexpected response format from API"
                }]
            }
    
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
                return {
                    "message": "Webhook processed",
                    "event": "wait_for_session",
                    "handlerCount": 1,
                    "results": [{
                        "success": False,
                        "error": f"Session {session_id} did not complete within {timeout_seconds} seconds"
                    }]
                }
            
            # Get session status
            status_response = await self.get_session_status(session_id)
            
            # Extract session status from webhook response
            if "results" in status_response and len(status_response.get("results", [])) > 0:
                first_result = status_response["results"][0]
                if first_result.get("success"):
                    session = first_result.get("data", {}).get("session", {})
                    session_status = session.get("status")
                    
                    if session_status in ["completed", "failed"]:
                        # Get final output if completed
                        if session_status == "completed":
                            output_response = await self.get_session_output(session_id)
                            if "results" in output_response and len(output_response.get("results", [])) > 0:
                                output_result = output_response["results"][0]
                                if output_result.get("success"):
                                    return {
                                        "message": "Webhook processed",
                                        "event": "wait_for_session",
                                        "handlerCount": 1,
                                        "results": [{
                                            "success": True,
                                            "data": {
                                                "sessionId": session_id,
                                                "status": "completed",
                                                "durationSeconds": int(asyncio.get_event_loop().time() - start_time),
                                                "output": output_result.get("data", {}).get("output", {})
                                            }
                                        }]
                                    }
                        else:
                            return {
                                "message": "Webhook processed",
                                "event": "wait_for_session",
                                "handlerCount": 1,
                                "results": [{
                                    "success": True,
                                    "data": {
                                        "sessionId": session_id,
                                        "status": "failed",
                                        "error": "Session failed",
                                        "durationSeconds": int(asyncio.get_event_loop().time() - start_time)
                                    }
                                }]
                            }
                else:
                    return status_response  # Return error response
            
            # Wait before next poll
            await asyncio.sleep(poll_interval_seconds)
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.client:
            await self.client.aclose()


# Initialize the orchestration client
orchestration = ClaudeOrchestrationMCP()


# Helper function to run async functions in sync context
def run_async(coro):
    """Run an async coroutine in a synchronous context, handling event loop issues"""
    try:
        # Check if there's already a running event loop
        loop = asyncio.get_running_loop()
        # If we have a running loop, use ThreadPoolExecutor to run in a new thread
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, coro)
            return future.result()
    except RuntimeError:
        # No event loop running, use asyncio.run normally
        return asyncio.run(coro)


# Gradio wrapper functions for async methods
def create_session_sync(session_type, repository, requirements, context="", branch="", dependencies="", auto_start=True, timeout_minutes=60):
    """Synchronous wrapper for create_session
    
    Args:
        session_type: Type of session (implementation, analysis, testing, review, coordination)
        repository: GitHub repository in format owner/repo
        requirements: Requirements for this session
        context: Additional context (optional)
        branch: Target branch (optional)
        dependencies: Comma-separated list of session IDs that must complete before this session starts (optional)
        auto_start: Whether to automatically start the session when dependencies are met
        timeout_minutes: Maximum runtime in minutes
    """
    deps_list = [d.strip() for d in dependencies.split(",") if d.strip()] if dependencies else None
    
    result = run_async(orchestration.create_session(
        session_type, 
        repository, 
        requirements, 
        context or None, 
        branch or None, 
        deps_list,
        auto_start,
        timeout_minutes if timeout_minutes else None
    ))
    
    return json.dumps(result, indent=2)


def start_session_sync(session_id: str) -> str:
    """Synchronous wrapper for start_session"""
    result = run_async(orchestration.start_session(session_id))
    return json.dumps(result, indent=2)


def get_session_status_sync(session_id: str) -> str:
    """Synchronous wrapper for get_session_status"""
    result = run_async(orchestration.get_session_status(session_id))
    return json.dumps(result, indent=2)


def get_session_output_sync(session_id: str) -> str:
    """Synchronous wrapper for get_session_output"""
    result = run_async(orchestration.get_session_output(session_id))
    return json.dumps(result, indent=2)


def list_sessions_sync(status: str = "all") -> str:
    """Synchronous wrapper for list_sessions"""
    result = run_async(orchestration.list_sessions(
        status if status != "all" else None
    ))
    return json.dumps(result, indent=2)


def wait_for_session_sync(session_id: str, timeout_seconds: float = 3600, poll_interval_seconds: float = 10) -> str:
    """Synchronous wrapper for wait_for_session"""
    result = run_async(orchestration.wait_for_session(
        session_id, int(timeout_seconds), int(poll_interval_seconds)
    ))
    return json.dumps(result, indent=2)


# Create Gradio interface
def create_gradio_interface():
    """Create the Gradio interface for the MCP server"""
    
    with gr.Blocks(title="Claude Orchestration MCP Server") as demo:
        gr.Markdown("# Claude Orchestration MCP Server")
        gr.Markdown("Orchestrate multiple Claude Code sessions for complex software projects")
        
        with gr.Tab("Create Session"):
            with gr.Row():
                with gr.Column():
                    session_type = gr.Dropdown(
                        choices=["implementation", "analysis", "testing", "review", "coordination"],
                        label="Session Type",
                        value="implementation"
                    )
                    repository = gr.Textbox(label="Repository (owner/repo)", placeholder="owner/repo")
                    requirements = gr.Textbox(
                        label="Requirements",
                        lines=5,
                        placeholder="Detailed requirements for this session..."
                    )
                    context = gr.Textbox(
                        label="Context (optional)",
                        lines=3,
                        placeholder="Additional context about the project..."
                    )
                    branch = gr.Textbox(
                        label="Branch (optional)",
                        placeholder="feature/new-feature"
                    )
                    dependencies = gr.Textbox(
                        label="Dependencies (optional, comma-separated session IDs)",
                        placeholder="session-id-1, session-id-2",
                        info="Enter session IDs that must complete before this session starts"
                    )
                    auto_start = gr.Checkbox(
                        label="Auto Start",
                        value=True,
                        info="Automatically start session when dependencies are met"
                    )
                    timeout_minutes = gr.Number(
                        label="Timeout (minutes)",
                        value=60,
                        info="Maximum runtime before session is terminated"
                    )
                    create_btn = gr.Button("Create Session", variant="primary")
                
                with gr.Column():
                    create_output = gr.Textbox(label="Result", lines=10)
            
            create_btn.click(
                create_session_sync,
                inputs=[session_type, repository, requirements, context, branch, dependencies, auto_start, timeout_minutes],
                outputs=create_output
            )
        
        with gr.Tab("Start Session"):
            with gr.Row():
                with gr.Column():
                    start_session_id = gr.Textbox(label="Session ID")
                    start_btn = gr.Button("Start Session", variant="primary")
                
                with gr.Column():
                    start_output = gr.Textbox(label="Result", lines=10)
            
            start_btn.click(
                start_session_sync,
                inputs=start_session_id,
                outputs=start_output
            )
        
        with gr.Tab("Get Status"):
            with gr.Row():
                with gr.Column():
                    status_session_id = gr.Textbox(label="Session ID")
                    status_btn = gr.Button("Get Status", variant="primary")
                
                with gr.Column():
                    status_output = gr.Textbox(label="Result", lines=10)
            
            status_btn.click(
                get_session_status_sync,
                inputs=status_session_id,
                outputs=status_output
            )
        
        with gr.Tab("Get Output"):
            with gr.Row():
                with gr.Column():
                    output_session_id = gr.Textbox(label="Session ID")
                    output_btn = gr.Button("Get Output", variant="primary")
                
                with gr.Column():
                    output_output = gr.Textbox(label="Result", lines=15)
            
            output_btn.click(
                get_session_output_sync,
                inputs=output_session_id,
                outputs=output_output
            )
        
        with gr.Tab("List Sessions"):
            with gr.Row():
                with gr.Column():
                    list_status = gr.Dropdown(
                        choices=["all", "pending", "initializing", "queued", "running", "completed", "failed", "cancelled"],
                        label="Status Filter",
                        value="all"
                    )
                    list_btn = gr.Button("List Sessions", variant="primary")
                
                with gr.Column():
                    list_output = gr.Textbox(label="Result", lines=15)
            
            list_btn.click(
                list_sessions_sync,
                inputs=[list_status],
                outputs=list_output
            )
        
        with gr.Tab("Wait for Session"):
            with gr.Row():
                with gr.Column():
                    wait_session_id = gr.Textbox(label="Session ID")
                    wait_timeout = gr.Number(label="Timeout (seconds)", value=3600)
                    wait_interval = gr.Number(label="Poll Interval (seconds)", value=10)
                    wait_btn = gr.Button("Wait for Completion", variant="primary")
                
                with gr.Column():
                    wait_output = gr.Textbox(label="Result", lines=15)
            
            wait_btn.click(
                wait_for_session_sync,
                inputs=[wait_session_id, wait_timeout, wait_interval],
                outputs=wait_output
            )
    
    return demo


# Main entry point
if __name__ == "__main__":
    print("Claude Orchestration MCP Server")
    print(f"API URL: {orchestration.api_url}")
    print(f"Auth configured: {'Yes' if orchestration.auth_token else 'No'}")
    print("\nStarting Gradio interface...")
    
    # Create and launch the interface
    demo = create_gradio_interface()
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False, mcp_server=True)