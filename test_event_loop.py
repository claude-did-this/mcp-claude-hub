#!/usr/bin/env python3
"""Test script to diagnose event loop issues in MCP server"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the orchestration client directly
from mcp_server import ClaudeOrchestrationMCP

async def test_create_sessions():
    """Test creating multiple sessions"""
    orchestration = ClaudeOrchestrationMCP()
    
    sessions = []
    
    # Test 1: Create first session
    print("Creating first session...")
    try:
        result1 = await orchestration.create_session(
            session_type="implementation",
            repository="Cheffromspace/demo-repository",
            requirements="Create a simple Python tutorial demonstrating basic concepts like variables, functions, and loops",
            context="Test of MCP tools - Python basics tutorial",
            dependencies=["python3"]
        )
        print(f"Session 1 created: {result1}")
        
        if result1.get("results", [{}])[0].get("success"):
            session1_id = result1["results"][0]["data"]["session"]["id"]
            sessions.append(session1_id)
            print(f"Session 1 ID: {session1_id}")
    except Exception as e:
        print(f"Error creating session 1: {e}")
    
    # Test 2: Create second session
    print("\nCreating second session...")
    try:
        result2 = await orchestration.create_session(
            session_type="implementation",
            repository="Cheffromspace/demo-repository",
            requirements="Create a Python tutorial on working with lists, dictionaries, and file I/O operations",
            context="Test of MCP tools - Data structures tutorial",
            dependencies=["python3", "requests"]
        )
        print(f"Session 2 created: {result2}")
        
        if result2.get("results", [{}])[0].get("success"):
            session2_id = result2["results"][0]["data"]["session"]["id"]
            sessions.append(session2_id)
            print(f"Session 2 ID: {session2_id}")
    except Exception as e:
        print(f"Error creating session 2: {e}")
    
    # Test 3: Start sessions
    for session_id in sessions:
        print(f"\nStarting session {session_id}...")
        try:
            start_result = await orchestration.start_session(session_id)
            print(f"Start result: {start_result}")
        except Exception as e:
            print(f"Error starting session: {e}")
    
    # Test 4: Get status
    for session_id in sessions:
        print(f"\nGetting status for session {session_id}...")
        try:
            status_result = await orchestration.get_session_status(session_id)
            print(f"Status result: {status_result}")
        except Exception as e:
            print(f"Error getting status: {e}")
    
    return sessions

if __name__ == "__main__":
    print("Testing Claude Hub MCP Event Loop")
    print(f"API URL: {os.getenv('CLAUDE_HUB_API_URL', 'http://localhost:3002/api/webhooks/claude')}")
    print(f"Auth configured: {'Yes' if os.getenv('CLAUDE_WEBHOOK_SECRET') else 'No'}")
    print("-" * 50)
    
    # Run the async test
    sessions = asyncio.run(test_create_sessions())
    print(f"\nCreated sessions: {sessions}")