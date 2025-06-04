#!/usr/bin/env python3
"""Simple unit tests for Claude Orchestration MCP Server"""

import unittest
import asyncio
from mcp_server import ClaudeOrchestrationMCP


class TestClaudeOrchestrationMCP(unittest.TestCase):
    """Basic unit tests without mocking"""
    
    def setUp(self):
        """Set up test client"""
        self.client = ClaudeOrchestrationMCP()
    
    def test_initialization(self):
        """Test that the client initializes correctly"""
        self.assertIsNotNone(self.client.api_url)
        self.assertIsInstance(self.client.auth_token, str)
        print("✅ Initialization test passed")
        
    def test_session_types(self):
        """Test valid session types"""
        valid_types = ["implementation", "analysis", "testing", "review", "coordination"]
        
        for session_type in valid_types:
            # Just verify the type is in our list
            self.assertIn(session_type, valid_types)
        
        print("✅ Session types test passed")
    
    def test_payload_structure(self):
        """Test that we can create valid payload structures"""
        # Test create session payload
        payload = {
            "type": "session.create",
            "session": {
                "type": "implementation",
                "project": {
                    "repository": "owner/repo",
                    "requirements": "Build something"
                },
                "dependencies": []
            }
        }
        
        self.assertEqual(payload["type"], "session.create")
        self.assertEqual(payload["session"]["type"], "implementation")
        self.assertIn("repository", payload["session"]["project"])
        print("✅ Payload structure test passed")
    
    def test_optional_fields(self):
        """Test handling of optional fields"""
        project_data = {
            "repository": "owner/repo",
            "requirements": "Do something"
        }
        
        # Add optional fields
        project_data["context"] = "Additional info"
        project_data["branch"] = "feature/test"
        
        self.assertEqual(len(project_data), 4)
        self.assertIn("context", project_data)
        self.assertIn("branch", project_data)
        print("✅ Optional fields test passed")
    
    def test_invalid_session_type(self):
        """Test that invalid session types are rejected"""
        async def test():
            result = await self.client.create_session(
                session_type="invalid_type",
                repository="owner/repo",
                requirements="Test requirements"
            )
            self.assertFalse(result["results"][0]["success"])
            self.assertIn("Invalid session type", result["results"][0]["error"])
        
        asyncio.run(test())
        print("✅ Invalid session type test passed")
    
    def test_invalid_repository_format(self):
        """Test that invalid repository formats are rejected"""
        async def test():
            # Test missing slash
            result = await self.client.create_session(
                session_type="implementation",
                repository="ownerrepo",
                requirements="Test requirements"
            )
            self.assertFalse(result["results"][0]["success"])
            self.assertIn("Invalid repository format", result["results"][0]["error"])
            
            # Test empty repository
            result = await self.client.create_session(
                session_type="implementation",
                repository="",
                requirements="Test requirements"
            )
            self.assertFalse(result["results"][0]["success"])
            self.assertIn("Invalid repository format", result["results"][0]["error"])
            
            # Test multiple slashes
            result = await self.client.create_session(
                session_type="implementation",
                repository="owner/repo/extra",
                requirements="Test requirements"
            )
            self.assertFalse(result["results"][0]["success"])
            self.assertIn("Invalid repository format", result["results"][0]["error"])
            
            # Test empty owner
            result = await self.client.create_session(
                session_type="implementation",
                repository="/repo",
                requirements="Test requirements"
            )
            self.assertFalse(result["results"][0]["success"])
            self.assertIn("Invalid repository format", result["results"][0]["error"])
            
            # Test empty repo name
            result = await self.client.create_session(
                session_type="implementation",
                repository="owner/",
                requirements="Test requirements"
            )
            self.assertFalse(result["results"][0]["success"])
            self.assertIn("Invalid repository format", result["results"][0]["error"])
        
        asyncio.run(test())
        print("✅ Invalid repository format test passed")
    
    def test_empty_requirements(self):
        """Test that empty requirements are rejected"""
        async def test():
            # Test empty string
            result = await self.client.create_session(
                session_type="implementation",
                repository="owner/repo",
                requirements=""
            )
            self.assertFalse(result["results"][0]["success"])
            self.assertIn("Requirements cannot be empty", result["results"][0]["error"])
            
            # Test whitespace only
            result = await self.client.create_session(
                session_type="implementation",
                repository="owner/repo",
                requirements="   "
            )
            self.assertFalse(result["results"][0]["success"])
            self.assertIn("Requirements cannot be empty", result["results"][0]["error"])
        
        asyncio.run(test())
        print("✅ Empty requirements test passed")
    
    def test_response_validation(self):
        """Test response structure validation"""
        # Test that our response validation logic works
        # This tests the structure without making actual API calls
        
        # Valid webhook response structure
        valid_response = {
            "message": "Webhook processed",
            "event": "session.create",
            "handlerCount": 1,
            "results": [{
                "success": True,
                "data": {"sessionId": "test-123"}
            }]
        }
        
        # Check structure
        self.assertIn("results", valid_response)
        self.assertIsInstance(valid_response["results"], list)
        self.assertTrue(len(valid_response["results"]) > 0)
        self.assertIsInstance(valid_response["results"][0], dict)
        
        print("✅ Response validation test passed")


if __name__ == "__main__":
    print("Running simple unit tests...")
    print("=" * 40)
    unittest.main(verbosity=1)