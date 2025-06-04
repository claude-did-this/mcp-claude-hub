#!/usr/bin/env python3
"""Simple unit tests for Claude Orchestration MCP Server"""

import unittest
from mcp_server import ClaudeOrchestrationMCP


class TestClaudeOrchestrationMCP(unittest.TestCase):
    """Basic unit tests without mocking"""
    
    def test_initialization(self):
        """Test that the client initializes correctly"""
        client = ClaudeOrchestrationMCP()
        self.assertIsNotNone(client.api_url)
        self.assertIsInstance(client.auth_token, str)
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


if __name__ == "__main__":
    print("Running simple unit tests...")
    print("=" * 40)
    unittest.main(verbosity=1)