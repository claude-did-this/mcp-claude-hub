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
            return response.json()
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
        
        # Check if response is in webhook handler format
        if "results" in result and len(result.get("results", [])) > 0:
            first_result = result["results"][0]
            if first_result.get("success"):
                session = first_result.get("data", {}).get("session", {})
                return {
                    "message": "Webhook processed",
                    "event": "session.create",
                    "handlerCount": 1,
                    "results": [{
                        "success": True,
                        "message": "Session created successfully",
                        "data": {
                            "session": {
                                "id": session.get("id"),
                                "type": session.get("type"),
                                "status": session.get("status", "initializing"),
                                "project": session.get("project", {}),
                                "dependencies": session.get("dependencies", []),
                                "containerId": session.get("containerId")
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
                "event": "session.create",
                "handlerCount": 1,
                "results": [{
                    "success": False,
                    "error": "Unexpected response format from API"
                }]
            }
    
    async def start_session(self, session_id: str) -> Dict[str, Any]:
        """Start a previously created session"""
        
        payload = {
            "type": "session.start",
            "sessionId": session_id
        }
        
        result = await self._make_request(payload)
        
        # Check if response is in webhook handler format
        if "results" in result and len(result.get("results", [])) > 0:
            first_result = result["results"][0]
            if first_result.get("success"):
                data = first_result.get("data", {})
                session = data.get("session", {})
                
                # Check if session was queued due to dependencies
                if "waitingFor" in data:
                    return {
                        "message": "Webhook processed",
                        "event": "session.start",
                        "handlerCount": 1,
                        "results": [{
                            "success": True,
                            "message": "Session queued, waiting for dependencies",
                            "data": {
                                "session": session,
                                "waitingFor": data.get("waitingFor", [])
                            }
                        }]
                    }
                else:
                    return {
                        "message": "Webhook processed",
                        "event": "session.start",
                        "handlerCount": 1,
                        "results": [{
                            "success": True,
                            "message": "Session started",
                            "data": {
                                "session": session
                            }
                        }]
                    }
            else:
                return result  # Return error response as-is
        else:
            # Fallback for unexpected response format
            return {
                "message": "Webhook processed",
                "event": "session.start",
                "handlerCount": 1,
                "results": [{
                    "success": False,
                    "error": "Unexpected response format from API"
                }]
            }
    
    async def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get the current status of a session"""
        
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
                                "project": session.get("project", {}),
                                "dependencies": session.get("dependencies", []),
                                "output": session.get("output", {})
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
        """Get the output from a completed session"""
        
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
                                "summary": output.get("summary", ""),
                                "filesCreated": output.get("filesCreated", []),
                                "filesModified": output.get("filesModified", []),
                                "testsRun": output.get("testsRun", False),
                                "testsPassed": output.get("testsPassed", False),
                                "errors": output.get("errors", []),
                                "logs": output.get("logs", ""),
                                "metrics": {
                                    "durationSeconds": output.get("metrics", {}).get("durationSeconds", 0),
                                    "tokensUsed": output.get("metrics", {}).get("tokensUsed", 0)
                                }
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
        """List all sessions, optionally filtered"""
        
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
def create_session_sync(session_type, repository, requirements, context="", dependencies=""):
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
                    session_type, repository, requirements, context or None, deps_list
                )
            )
            result = future.result()
    except RuntimeError:
        # No event loop running, use asyncio.run normally
        result = asyncio.run(orchestration.create_session(
            session_type, repository, requirements, context or None, deps_list
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
                        choices=["implementation", "analysis", "testing", "review", "documentation"],
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
                    dependencies = gr.Textbox(
                        label="Dependencies (comma-separated session IDs)",
                        placeholder="session-id-1, session-id-2"
                    )
                    create_btn = gr.Button("Create Session", variant="primary")
                
                with gr.Column():
                    create_output = gr.Textbox(label="Result", lines=10)
            
            create_btn.click(
                create_session_sync,
                inputs=[session_type, repository, requirements, context, dependencies],
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
                        choices=["all", "pending", "initializing", "queued", "running", "completed", "failed"],
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