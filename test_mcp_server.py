"""
Test script for the Claude Orchestration MCP Server
"""

import asyncio
from mcp_server import ClaudeOrchestrationMCP
import json


async def test_orchestration():
    """Test the orchestration functionality"""
    
    print("Claude Orchestration MCP Server Test")
    print("=" * 50)
    
    # Initialize the orchestration client
    client = ClaudeOrchestrationMCP()
    
    print(f"\nAPI URL: {client.api_url}")
    print(f"Auth configured: {'Yes' if client.auth_token else 'No'}")
    
    # Test 1: Create a session
    print("\n1. Testing create_session...")
    try:
        response = await client.create_session(
            session_type="implementation",
            repository="test/repo",
            requirements="Build a simple REST API",
            context="Test project for MCP server"
        )
        print(f"✓ Session created: {json.dumps(response, indent=2)}")
        
        # Extract session_id from webhook response format
        session_id = None
        if "results" in response and len(response.get("results", [])) > 0:
            first_result = response["results"][0]
            if first_result.get("success"):
                session_id = first_result.get("data", {}).get("session", {}).get("id")
        
        if session_id:
            print(f"  Session ID: {session_id}")
        else:
            print("  Warning: Could not extract session ID from response")
            
    except Exception as e:
        print(f"✗ Failed to create session: {e}")
        session_id = None
    
    # Test 2: Start the session
    if session_id:
        print("\n2. Testing start_session...")
        try:
            result = await client.start_session(session_id)
            print(f"✓ Session started: {json.dumps(result, indent=2)}")
            
            # Check if session was queued
            if "results" in result and len(result.get("results", [])) > 0:
                first_result = result["results"][0]
                if first_result.get("success"):
                    data = first_result.get("data", {})
                    if "waitingFor" in data:
                        print(f"  Status: Queued, waiting for dependencies: {data['waitingFor']}")
                    else:
                        print("  Status: Started successfully")
        except Exception as e:
            print(f"✗ Failed to start session: {e}")
    
    # Test 3: Get session status
    if session_id:
        print("\n3. Testing get_session_status...")
        try:
            status = await client.get_session_status(session_id)
            print(f"✓ Session status: {json.dumps(status, indent=2)}")
            
            # Extract and display key status info
            if "results" in status and len(status.get("results", [])) > 0:
                first_result = status["results"][0]
                if first_result.get("success"):
                    session = first_result.get("data", {}).get("session", {})
                    print(f"  Current status: {session.get('status')}")
                    print(f"  Type: {session.get('type')}")
        except Exception as e:
            print(f"✗ Failed to get session status: {e}")
    
    # Test 4: List sessions
    print("\n4. Testing list_sessions...")
    try:
        sessions = await client.list_sessions()
        print(f"✓ Sessions listed: {json.dumps(sessions, indent=2)}")
        
        # Display session count
        if "results" in sessions and len(sessions.get("results", [])) > 0:
            first_result = sessions["results"][0]
            if first_result.get("success"):
                session_list = first_result.get("data", {}).get("sessions", [])
                print(f"  Total sessions: {len(session_list)}")
    except Exception as e:
        print(f"✗ Failed to list sessions: {e}")
    
    # Close the client
    await client.client.aclose()
    
    print("\n" + "=" * 50)
    print("Test complete!")


if __name__ == "__main__":
    # Run the async test
    asyncio.run(test_orchestration())