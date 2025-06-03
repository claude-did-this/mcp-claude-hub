# MCP Server Specification for Claude Orchestration

This document provides a complete specification for implementing an MCP (Model Context Protocol) server that exposes Claude orchestration endpoints using the Gradio MCP library.

## Overview

The MCP server will provide tools for orchestrating multiple Claude Code sessions to work on complex projects in parallel. The server acts as a bridge between Claude (as an MCP client) and the Claude Hub webhook API.

## Prerequisites

- Gradio MCP library
- Python 3.8+
- Access to Claude Hub API endpoint
- API authentication token

## Endpoints to Implement

### Base Configuration

```python
CLAUDE_HUB_API_URL = "https://your-claude-hub.com/api/webhooks/claude"
CLAUDE_WEBHOOK_SECRET = "your-webhook-secret"
```

## MCP Tools Specification

### 1. `create_session`

Creates a new Claude Code session for a specific subtask.

**Parameters:**
```json
{
  "session_type": {
    "type": "string",
    "enum": ["implementation", "analysis", "testing", "review", "documentation"],
    "description": "Type of session to create based on the task",
    "required": true
  },
  "repository": {
    "type": "string",
    "description": "Repository in format 'owner/repo'",
    "required": true
  },
  "requirements": {
    "type": "string", 
    "description": "Detailed requirements for this specific session",
    "required": true
  },
  "context": {
    "type": "string",
    "description": "Additional context about the overall project",
    "required": false
  },
  "dependencies": {
    "type": "array",
    "items": {"type": "string"},
    "description": "Array of session IDs that must complete before this session starts",
    "required": false,
    "default": []
  }
}
```

**API Call:**
```python
POST /api/webhooks/claude
Headers:
  - Authorization: Bearer {token}
  - Content-Type: application/json

Body:
{
  "type": "session.create",
  "session": {
    "type": "{session_type}",
    "project": {
      "repository": "{repository}",
      "requirements": "{requirements}",
      "context": "{context}"
    },
    "dependencies": {dependencies}
  }
}
```

**Returns:**
```json
{
  "session_id": "uuid-string",
  "status": "pending",
  "type": "implementation",
  "container_id": "docker-container-id"
}
```

### 2. `start_session`

Starts a previously created session or queues it if dependencies aren't met.

**Parameters:**
```json
{
  "session_id": {
    "type": "string",
    "description": "The ID of the session to start",
    "required": true
  }
}
```

**API Call:**
```python
POST /api/webhooks/claude
Body:
{
  "type": "session.start",
  "sessionId": "{session_id}"
}
```

**Returns:**
```json
{
  "started": true,
  "status": "running",  // or "queued" if dependencies not met
  "message": "Session started successfully"
}
```

### 3. `get_session_status`

Retrieves the current status and details of a session.

**Parameters:**
```json
{
  "session_id": {
    "type": "string",
    "description": "The ID of the session to check",
    "required": true
  }
}
```

**API Call:**
```python
POST /api/webhooks/claude
Body:
{
  "type": "session.get",
  "sessionId": "{session_id}"
}
```

**Returns:**
```json
{
  "session_id": "uuid-string",
  "status": "running",  // pending, initializing, running, completed, failed
  "type": "implementation",
  "progress": "Working on authentication module...",
  "created_at": "2024-01-20T10:30:00Z",
  "started_at": "2024-01-20T10:31:00Z",
  "container_id": "docker-container-id"
}
```

### 4. `get_session_output`

Retrieves the output and results from a completed session.

**Parameters:**
```json
{
  "session_id": {
    "type": "string",
    "description": "The ID of the completed session",
    "required": true
  }
}
```

**API Call:**
```python
POST /api/webhooks/claude
Body:
{
  "type": "session.output",
  "sessionId": "{session_id}"
}
```

**Returns:**
```json
{
  "session_id": "uuid-string",
  "status": "completed",
  "output": {
    "summary": "Implemented JWT authentication with refresh tokens",
    "files_created": [
      "src/auth/jwt.ts",
      "src/auth/middleware.ts",
      "tests/auth.test.ts"
    ],
    "files_modified": [
      "src/index.ts",
      "package.json"
    ],
    "tests_passed": true,
    "errors": [],
    "logs": "...",
    "metrics": {
      "duration_seconds": 245,
      "tokens_used": 15000
    }
  }
}
```

### 5. `list_sessions`

Lists all sessions, optionally filtered by orchestration ID.

**Parameters:**
```json
{
  "orchestration_id": {
    "type": "string",
    "description": "Optional orchestration ID to filter sessions",
    "required": false
  },
  "status": {
    "type": "string",
    "enum": ["pending", "running", "completed", "failed", "all"],
    "description": "Filter by session status",
    "required": false,
    "default": "all"
  }
}
```

**API Call:**
```python
POST /api/webhooks/claude
Body:
{
  "type": "session.list",
  "orchestrationId": "{orchestration_id}"  // optional
}
```

**Returns:**
```json
{
  "sessions": [
    {
      "session_id": "uuid-1",
      "type": "implementation",
      "status": "completed",
      "description": "Authentication module",
      "created_at": "2024-01-20T10:30:00Z"
    },
    {
      "session_id": "uuid-2",
      "type": "implementation", 
      "status": "running",
      "description": "API endpoints",
      "created_at": "2024-01-20T10:35:00Z",
      "dependencies": ["uuid-1"]
    }
  ],
  "total": 2
}
```

### 6. `wait_for_session`

Waits for a session to complete (polling helper).

**Parameters:**
```json
{
  "session_id": {
    "type": "string",
    "description": "The ID of the session to wait for",
    "required": true
  },
  "timeout_seconds": {
    "type": "integer",
    "description": "Maximum time to wait in seconds",
    "required": false,
    "default": 3600
  },
  "poll_interval_seconds": {
    "type": "integer",
    "description": "How often to check status",
    "required": false,
    "default": 10
  }
}
```

**Returns:**
```json
{
  "session_id": "uuid-string",
  "status": "completed",
  "duration_seconds": 245,
  "output": { ... }  // Same as get_session_output
}
```

## Implementation Guide

### 1. Basic MCP Server Structure

```python
from gradio_mcp import MCPServer
import httpx
import asyncio
from typing import Dict, List, Optional, Any

class ClaudeOrchestrationMCP:
    def __init__(self, api_url: str, auth_token: str):
        self.api_url = api_url
        self.auth_token = auth_token
        self.client = httpx.AsyncClient()
        
    async def create_session(
        self,
        session_type: str,
        repository: str,
        requirements: str,
        context: Optional[str] = None,
        dependencies: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a new Claude Code session"""
        # Implementation here
        
    async def start_session(self, session_id: str) -> Dict[str, Any]:
        """Start a created session"""
        # Implementation here
        
    # ... other methods
```

### 2. Gradio MCP Integration

```python
# Initialize the MCP server
mcp_server = MCPServer(
    name="claude-orchestration",
    description="Orchestrate multiple Claude Code sessions for complex projects"
)

# Register tools
mcp_server.register_tool(
    name="create_session",
    function=orchestration.create_session,
    description="Create a new Claude Code session for a subtask",
    parameters={...}  # As specified above
)

# ... register other tools
```

### 3. Error Handling

The MCP server should handle these error cases gracefully:

- **Authentication failures**: Return clear error message
- **Session not found**: Return helpful error with available session IDs
- **Dependencies not met**: Return status indicating session is queued
- **API timeouts**: Implement retry logic with exponential backoff
- **Invalid parameters**: Validate inputs before making API calls

### 4. Best Practices

1. **Session Naming**: Generate descriptive session IDs that indicate their purpose
2. **Dependency Tracking**: Maintain a graph of session dependencies
3. **Progress Updates**: Poll running sessions periodically for status updates
4. **Resource Management**: Implement limits on concurrent sessions
5. **Logging**: Log all session operations for debugging

## Example Usage Flow

Here's how Claude would use these tools to build a full-stack application:

```python
# 1. Create backend session
backend_session = await create_session(
    session_type="implementation",
    repository="owner/myapp",
    requirements="Create Express.js backend with PostgreSQL database models for user management",
    context="Building a task management app"
)

# 2. Start backend development
await start_session(backend_session["session_id"])

# 3. Create frontend session (depends on backend)
frontend_session = await create_session(
    session_type="implementation",
    repository="owner/myapp",
    requirements="Create React frontend with Material-UI that connects to the backend API",
    dependencies=[backend_session["session_id"]]
)

# 4. Wait for backend to complete
backend_result = await wait_for_session(
    backend_session["session_id"],
    timeout_seconds=1800
)

# 5. Frontend automatically starts when backend completes
# Check frontend progress
frontend_status = await get_session_status(frontend_session["session_id"])

# 6. Create test session after both complete
test_session = await create_session(
    session_type="testing",
    repository="owner/myapp",
    requirements="Write comprehensive tests for both frontend and backend",
    dependencies=[
        backend_session["session_id"],
        frontend_session["session_id"]
    ]
)
```

## Testing the MCP Server

1. **Unit Tests**: Test each tool function independently
2. **Integration Tests**: Test full orchestration workflows
3. **Error Cases**: Test handling of failures and edge cases
4. **Performance Tests**: Ensure the server can handle multiple concurrent orchestrations

## Security Considerations

1. **Authentication**: Always validate the auth token
2. **Input Validation**: Sanitize all inputs to prevent injection
3. **Rate Limiting**: Implement rate limiting to prevent abuse
4. **Session Isolation**: Ensure sessions cannot access each other's data
5. **Audit Logging**: Log all operations for security monitoring

## Deployment

The MCP server can be deployed as:

1. **Standalone Service**: Run as a separate Python service
2. **Gradio App**: Deploy as a Gradio application
3. **Serverless Function**: Deploy on AWS Lambda, Vercel, etc.
4. **Container**: Package as Docker container for flexibility

## Monitoring

Track these metrics:

- Number of active sessions
- Session completion rates
- Average session duration
- Error rates by type
- API response times
- Resource usage per session