# MCP Claude Hub Testing Bug Report

## Executive Summary
During testing of the MCP Claude Hub tools, several issues were encountered that prevent the full orchestration workflow from functioning as expected. While the API communication works correctly, the actual container orchestration appears to be incomplete.

## Issues Identified

### 1. Event Loop Closure Error
**Severity**: High  
**Status**: Fixed  
**Description**: When using MCP tools through the sync wrappers, the event loop would close prematurely.  
**Error**: `Event loop is closed`  
**Solution**: Implemented proper event loop handling using `nest_asyncio` and improved the sync wrapper functions in `mcp_server_fixed.py`.

### 2. Missing Orchestration ID Parameter
**Severity**: Medium  
**Status**: Identified  
**Description**: The `list_sessions_sync` tool requires an `orchestration_id` parameter but the API design suggests it should be optional.  
**Current Behavior**: Returns error when orchestration_id is not provided.  
**Expected Behavior**: Should list all sessions when no orchestration_id is provided.

### 3. Container Creation but No Execution
**Severity**: Critical  
**Status**: Open  
**Description**: Sessions are created successfully through the API, but the corresponding Docker containers are not being started or executed.
**Evidence**:
- API returns successful session creation with container IDs
- Webhook logs show "Container resources created"
- No actual Docker containers are running (`docker ps` shows only the webhook container)
- Sessions remain in "initializing" status indefinitely

### 4. Dependency Resolution Not Triggering
**Severity**: High  
**Status**: Open  
**Description**: When sessions are started, they report "waiting for dependencies" but the dependency resolution mechanism doesn't appear to trigger container startup.
**Current Behavior**: Sessions with dependencies like "python3" remain in waiting state.
**Expected Behavior**: Dependencies should be resolved and containers should start.

## Test Results

### Successful Operations
1. ✅ `create_session_sync` - Creates sessions successfully
2. ✅ `start_session_sync` - Accepts start requests
3. ✅ `get_session_status_sync` - Retrieves session status
4. ✅ `list_sessions_sync` - Lists sessions (when no orchestration_id filter)
5. ✅ API communication and authentication working correctly

### Failed Operations
1. ❌ Actual container startup and execution
2. ❌ Dependency resolution and container orchestration
3. ❌ Session progression from "initializing" to "running" state
4. ❌ Session completion and output retrieval

## Sessions Created During Testing
- Session 1: `8d13d88b-e1e5-4a87-8349-e38c10e147d8` - Python basics tutorial
- Session 2: `b005fad6-b408-408c-b424-b8514b6dfae5` - Python data structures tutorial

Both sessions remain in "initializing" state with containers created but not started.

## Recommendations

1. **Investigate Container Lifecycle Management**: The webhook creates container resources but doesn't appear to start them. Check the container startup logic in the webhook handler.

2. **Debug Dependency Resolution**: The "waiting for dependencies" state suggests there's a dependency resolver that should trigger container startup but isn't functioning.

3. **Add Container Status Logging**: More detailed logging around container lifecycle events would help diagnose why containers aren't starting.

4. **Review Docker Configuration**: Ensure the webhook has proper Docker socket permissions and the claudecode:latest image is properly configured for execution.

5. **Implement Health Checks**: Add health checks for the container orchestration system to detect when containers fail to start.

## Technical Details

### Environment
- API URL: https://claude.jonathanflatt.org/api/webhooks/claude
- Docker Host: 192.168.1.2
- Webhook Container: claude-repo-webhook-1 (running)
- Claude Image: claudecode:latest (exists)

### API Response Format
The API consistently returns well-structured responses in webhook handler format, indicating the API layer is functioning correctly. The issue appears to be in the container orchestration layer.

## Conclusion
While the MCP Claude Hub API integration is working correctly, the actual container orchestration functionality is not operational. Sessions are created but never progress beyond initialization, preventing the intended workflow of parallel Claude Code execution.