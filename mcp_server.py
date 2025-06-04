"""
Claude Orchestration MCP Server

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
            data = response.json()
            
            # If the response has a standard API format, convert to webhook format
            if "success" in data and "results" not in data:
                return {
                    "message": "Webhook processed" if data["success"] else "Webhook processing failed",
                    "event": payload.get("type", "unknown"),
                    "handlerCount": 1 if data["success"] else 0,
                    "results": [{
                        "success": data["success"],
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
        dependencies: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a new Claude Code session for a specific subtask
        
        Args:
            session_type: Type of session - implementation, analysis, testing, review, or coordination
            repository: GitHub repository in "owner/repo" format
            requirements: Clear description of what Claude should do
            context: Additional context about the codebase or requirements
            branch: Target branch name (defaults to main/master)
            dependencies: Array of session IDs that must complete before this session starts
        """
        
        project_data = {
            "repository": repository,
            "requirements": requirements
        }
        
        if context:
            project_data["context"] = context
        
        if branch:
            project_data["branch"] = branch
            
        payload = {
            "type": "session.create",
            "session": {
                "type": session_type,
                "project": project_data,
                "dependencies": dependencies or []
            }
        }
        
        result = await self._make_request(payload)
        
        # Extract data from webhook response
        if "results" in result and len(result.get("results", [])) > 0:
            first_result = result["results"][0]
            if first_result.get("success"):
                data = first_result.get("data", {})
                # Ensure we have the expected structure
                if "sessionId" in data or "session" in data:
                    session_id = data.get("sessionId") or data.get("session", {}).get("id")
                    return {
                        "message": "Webhook processed",
                        "event": "session.create",
                        "handlerCount": 1,
                        "results": [{
                            "success": True,
                            "message": "Session created",
                            "data": {
                                "sessionId": session_id,
                                "status": data.get("status", "pending")
                            }
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
                status = data.get("status", "initializing")
                
                return {
                    "message": "Webhook processed",
                    "event": "session.start",
                    "handlerCount": 1,
                    "results": [{
                        "success": True,
                        "message": "Session starting" if status == "initializing" else f"Session {status}",
                        "data": {
                            "status": status
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
                session = first_result.get("data", {}).get("session", {})
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
                output = data.get("output", {})
                return {
                    "message": "Webhook processed",
                    "event": "session.output",
                    "handlerCount": 1,
                    "results": [{
                        "success": True,
                        "data": {
                            "sessionId": data.get("sessionId", session_id),
                            "status": data.get("status", "completed"),
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
        orchestration_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """List all sessions, optionally filtered by orchestration ID
        
        Args:
            orchestration_id: Filter sessions by orchestration ID
            status: Filter by status (pending, initializing, running, completed, failed, cancelled, queued)
        """
        
        payload = {
            "type": "session.list"
        }
        
        if orchestration_id:
            payload["orchestrationId"] = orchestration_id
            
        result = await self._make_request(payload)
        
        # Check if response is in webhook handler format
        if "results" in result and len(result.get("results", [])) > 0:
            first_result = result["results"][0]
            if first_result.get("success"):
                sessions = first_result.get("data", {}).get("sessions", [])
                
                # Filter by status if requested
                if status and status != "all":
                    sessions = [s for s in sessions if s.get("status") == status]
                
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


# Initialize the orchestration client
orchestration = ClaudeOrchestrationMCP()


# Gradio wrapper functions for async methods
def create_session_sync(session_type, repository, requirements, context="", branch="", dependencies=""):
    """Synchronous wrapper for create_session"""
    deps_list = [d.strip() for d in dependencies.split(",") if d.strip()] if dependencies else None
    
    # Get the current event loop or create a new one
    try:
        loop = asyncio.get_running_loop()
        # If we have a running loop, create a task and run it
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(
                asyncio.run,
                orchestration.create_session(
                    session_type, repository, requirements, context or None, branch or None, deps_list
                )
            )
            result = future.result()
    except RuntimeError:
        # No event loop running, use asyncio.run normally
        result = asyncio.run(orchestration.create_session(
            session_type, repository, requirements, context or None, branch or None, deps_list
        ))
    
    return json.dumps(result, indent=2)


def start_session_sync(session_id):
    """Synchronous wrapper for start_session"""
    try:
        loop = asyncio.get_running_loop()
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(
                asyncio.run,
                orchestration.start_session(session_id)
            )
            result = future.result()
    except RuntimeError:
        result = asyncio.run(orchestration.start_session(session_id))
    
    return json.dumps(result, indent=2)


def get_session_status_sync(session_id):
    """Synchronous wrapper for get_session_status"""
    try:
        loop = asyncio.get_running_loop()
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(
                asyncio.run,
                orchestration.get_session_status(session_id)
            )
            result = future.result()
    except RuntimeError:
        result = asyncio.run(orchestration.get_session_status(session_id))
    
    return json.dumps(result, indent=2)


def get_session_output_sync(session_id):
    """Synchronous wrapper for get_session_output"""
    try:
        loop = asyncio.get_running_loop()
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(
                asyncio.run,
                orchestration.get_session_output(session_id)
            )
            result = future.result()
    except RuntimeError:
        result = asyncio.run(orchestration.get_session_output(session_id))
    
    return json.dumps(result, indent=2)


def list_sessions_sync(orchestration_id="", status="all"):
    """Synchronous wrapper for list_sessions"""
    try:
        loop = asyncio.get_running_loop()
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(
                asyncio.run,
                orchestration.list_sessions(
                    orchestration_id or None, status if status != "all" else None
                )
            )
            result = future.result()
    except RuntimeError:
        result = asyncio.run(orchestration.list_sessions(
            orchestration_id or None, status if status != "all" else None
        ))
    
    return json.dumps(result, indent=2)


def wait_for_session_sync(session_id, timeout_seconds=3600, poll_interval_seconds=10):
    """Synchronous wrapper for wait_for_session"""
    try:
        loop = asyncio.get_running_loop()
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(
                asyncio.run,
                orchestration.wait_for_session(
                    session_id, int(timeout_seconds), int(poll_interval_seconds)
                )
            )
            result = future.result()
    except RuntimeError:
        result = asyncio.run(orchestration.wait_for_session(
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
                        label="Dependencies (comma-separated session IDs)",
                        placeholder="session-id-1, session-id-2"
                    )
                    create_btn = gr.Button("Create Session", variant="primary")
                
                with gr.Column():
                    create_output = gr.Textbox(label="Result", lines=10)
            
            create_btn.click(
                create_session_sync,
                inputs=[session_type, repository, requirements, context, branch, dependencies],
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
                    list_orchestration_id = gr.Textbox(
                        label="Orchestration ID (optional)",
                        placeholder="Leave empty to list all"
                    )
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
                inputs=[list_orchestration_id, list_status],
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