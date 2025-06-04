#!/usr/bin/env python3
"""Simple smoke tests for Claude Orchestration MCP Server"""

import asyncio
import os
from mcp_server import ClaudeOrchestrationMCP
import json


def print_test_header(test_name):
    """Print a formatted test header"""
    print(f"\n{'='*50}")
    print(f"TEST: {test_name}")
    print(f"{'='*50}")


def check_response(response, test_name):
    """Check if response indicates success"""
    if "results" in response and response["results"]:
        result = response["results"][0]
        if result.get("success"):
            print(f"✅ {test_name}: PASSED")
            return True
        else:
            print(f"❌ {test_name}: FAILED - {result.get('error', 'Unknown error')}")
            return False
    else:
        print(f"❌ {test_name}: FAILED - Invalid response format")
        return False


async def run_smoke_tests():
    """Run basic smoke tests to ensure nothing is broken"""
    
    print("\nClaude Orchestration MCP Server - Smoke Tests")
    print("=" * 60)
    
    # Initialize client
    client = ClaudeOrchestrationMCP()
    print(f"API URL: {client.api_url}")
    print(f"Auth configured: {'Yes' if client.auth_token else 'No'}")
    
    if not client.auth_token:
        print("\n⚠️  WARNING: No auth token configured. Set CLAUDE_WEBHOOK_SECRET env var.")
        return
    
    results = {"passed": 0, "failed": 0}
    
    # Test 1: Create a simple session
    print_test_header("Create Session")
    try:
        response = await client.create_session(
            session_type="implementation",
            repository="test/repo",
            requirements="Test requirement",
            context="Test context"
        )
        if check_response(response, "Create Session"):
            results["passed"] += 1
            # Extract session ID for further tests
            session_id = response["results"][0]["data"].get("sessionId")
            print(f"   Session ID: {session_id}")
        else:
            results["failed"] += 1
            session_id = None
    except Exception as e:
        print(f"❌ Create Session: FAILED - Exception: {e}")
        results["failed"] += 1
        session_id = None
    
    # Test 2: List sessions
    print_test_header("List Sessions")
    try:
        response = await client.list_sessions()
        if check_response(response, "List Sessions"):
            results["passed"] += 1
            sessions = response["results"][0]["data"].get("sessions", [])
            print(f"   Found {len(sessions)} sessions")
        else:
            results["failed"] += 1
    except Exception as e:
        print(f"❌ List Sessions: FAILED - Exception: {e}")
        results["failed"] += 1
    
    # Test 3: Get session status (if we have a session ID)
    if session_id:
        print_test_header("Get Session Status")
        try:
            response = await client.get_session_status(session_id)
            if check_response(response, "Get Session Status"):
                results["passed"] += 1
                session = response["results"][0]["data"].get("session", {})
                print(f"   Status: {session.get('status', 'unknown')}")
            else:
                results["failed"] += 1
        except Exception as e:
            print(f"❌ Get Session Status: FAILED - Exception: {e}")
            results["failed"] += 1
    
    # Test 4: Create session with dependencies
    print_test_header("Create Session with Dependencies")
    try:
        response = await client.create_session(
            session_type="testing",
            repository="test/repo",
            requirements="Run tests",
            dependencies=[session_id] if session_id else []
        )
        if check_response(response, "Create Session with Dependencies"):
            results["passed"] += 1
        else:
            results["failed"] += 1
    except Exception as e:
        print(f"❌ Create Session with Dependencies: FAILED - Exception: {e}")
        results["failed"] += 1
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY:")
    print(f"✅ Passed: {results['passed']}")
    print(f"❌ Failed: {results['failed']}")
    print(f"Total: {results['passed'] + results['failed']}")
    print("=" * 60)
    
    return results["failed"] == 0


if __name__ == "__main__":
    # Run the async tests
    success = asyncio.run(run_smoke_tests())
    exit(0 if success else 1)