"""
Example: Using Claude Orchestration MCP Server

This example shows how Claude would use the MCP tools to orchestrate
building a full-stack Todo application with multiple parallel sessions.
"""

async def orchestrate_todo_app(mcp_client):
    """
    Example orchestration flow for building a full-stack Todo app.
    This is what Claude would do when given a complex project.
    """
    
    print("🚀 Starting Todo App Orchestration")
    
    # Phase 1: Core Backend Development
    print("\n📦 Phase 1: Creating backend session...")
    backend_session = await mcp_client.create_session(
        session_type="implementation",
        repository="user/todo-app",
        requirements="""
        Create a Node.js/Express backend with:
        - RESTful API endpoints for todos (CRUD operations)
        - PostgreSQL database with Prisma ORM
        - User authentication using JWT
        - Input validation and error handling
        - Organized folder structure following best practices
        """,
        context="Building a modern full-stack todo application with React frontend"
    )
    print(f"✅ Backend session created: {backend_session['session_id']}")
    
    # Start backend development
    await mcp_client.start_session(backend_session['session_id'])
    print("🔨 Backend development started...")
    
    # Phase 2: Database and Auth (can run in parallel with backend)
    print("\n📦 Phase 2: Creating database schema session...")
    db_session = await mcp_client.create_session(
        session_type="implementation",
        repository="user/todo-app",
        requirements="""
        Design and implement PostgreSQL database:
        - Users table with authentication fields
        - Todos table with user relationships
        - Proper indexes for performance
        - Migration files using Prisma
        - Seed data for testing
        """,
        context="Database layer for todo application"
    )
    
    await mcp_client.start_session(db_session['session_id'])
    print("🔨 Database development started...")
    
    # Wait for backend to complete before starting frontend
    print("\n⏳ Waiting for backend to complete...")
    backend_result = await mcp_client.wait_for_session(
        backend_session['session_id'],
        timeout_seconds=1800,
        poll_interval_seconds=15
    )
    print(f"✅ Backend completed in {backend_result['duration_seconds']}s")
    
    # Phase 3: Frontend Development (depends on backend API)
    print("\n📦 Phase 3: Creating frontend session...")
    frontend_session = await mcp_client.create_session(
        session_type="implementation",
        repository="user/todo-app",
        requirements="""
        Create a React frontend with:
        - Modern UI using Tailwind CSS
        - Todo list with add, edit, delete, complete functionality  
        - User authentication flow (login, register, logout)
        - API integration with the backend
        - Responsive design for mobile and desktop
        - Loading states and error handling
        """,
        context="React frontend for todo application",
        dependencies=[backend_session['session_id']]  # Wait for backend
    )
    
    await mcp_client.start_session(frontend_session['session_id'])
    print("🔨 Frontend development started...")
    
    # Phase 4: Testing Suite (depends on both backend and frontend)
    print("\n📦 Phase 4: Creating testing session...")
    testing_session = await mcp_client.create_session(
        session_type="testing",
        repository="user/todo-app",
        requirements="""
        Create comprehensive test suite:
        - Unit tests for backend API endpoints
        - Integration tests for database operations
        - Frontend component tests using React Testing Library
        - End-to-end tests using Playwright
        - Test user authentication flows
        - Achieve at least 80% code coverage
        """,
        context="Testing suite for todo application",
        dependencies=[
            backend_session['session_id'],
            frontend_session['session_id']
        ]
    )
    
    # Phase 5: Documentation (can start immediately)
    print("\n📦 Phase 5: Creating documentation session...")
    docs_session = await mcp_client.create_session(
        session_type="documentation",
        repository="user/todo-app",
        requirements="""
        Create project documentation:
        - README with setup instructions
        - API documentation with examples
        - Architecture overview diagram
        - Deployment guide
        - Contributing guidelines
        """,
        context="Documentation for todo application"
    )
    
    await mcp_client.start_session(docs_session['session_id'])
    print("📝 Documentation generation started...")
    
    # Monitor all sessions
    print("\n📊 Monitoring all sessions...")
    all_sessions = [
        backend_session,
        db_session,
        frontend_session,
        testing_session,
        docs_session
    ]
    
    completed_sessions = []
    failed_sessions = []
    
    # Wait for all sessions to complete
    for session in all_sessions:
        try:
            result = await mcp_client.wait_for_session(
                session['session_id'],
                timeout_seconds=3600
            )
            completed_sessions.append(result)
            print(f"✅ Session {session['session_id']} completed")
            
            # Get detailed output
            output = await mcp_client.get_session_output(session['session_id'])
            if output['output'].get('files_created'):
                print(f"   Created: {', '.join(output['output']['files_created'][:3])}...")
                
        except Exception as e:
            failed_sessions.append(session)
            print(f"❌ Session {session['session_id']} failed: {str(e)}")
    
    # Final summary
    print("\n🎉 Orchestration Complete!")
    print(f"✅ Successful sessions: {len(completed_sessions)}")
    print(f"❌ Failed sessions: {len(failed_sessions)}")
    
    # Get final session list
    final_sessions = await mcp_client.list_sessions()
    print(f"📊 Total sessions created: {final_sessions['total']}")
    
    return {
        "completed": completed_sessions,
        "failed": failed_sessions,
        "summary": "Todo application built successfully with all components"
    }


# Example of how Claude would break down a complex request
async def intelligent_task_decomposition(mcp_client, user_request):
    """
    This shows how Claude would intelligently decompose a user's request
    into multiple parallel sessions based on the requirements.
    """
    
    # Claude analyzes the request and identifies components
    print("🤔 Analyzing project requirements...")
    
    # Example: User says "Build me a social media app like Twitter"
    components = {
        "backend_api": {
            "priority": 1,
            "dependencies": [],
            "requirements": "Build REST API with user posts, follows, likes"
        },
        "database": {
            "priority": 1,
            "dependencies": [],
            "requirements": "Design scalable database schema for social features"
        },
        "auth_service": {
            "priority": 1,
            "dependencies": [],
            "requirements": "Implement OAuth and JWT authentication"
        },
        "frontend_web": {
            "priority": 2,
            "dependencies": ["backend_api"],
            "requirements": "Create responsive React web application"
        },
        "mobile_app": {
            "priority": 2,
            "dependencies": ["backend_api"],
            "requirements": "Build React Native mobile app"
        },
        "real_time": {
            "priority": 3,
            "dependencies": ["backend_api"],
            "requirements": "Add WebSocket support for real-time updates"
        },
        "testing": {
            "priority": 4,
            "dependencies": ["backend_api", "frontend_web"],
            "requirements": "Comprehensive test suite with >80% coverage"
        }
    }
    
    # Create sessions based on priority and dependencies
    sessions = {}
    
    for component_name, config in components.items():
        session = await mcp_client.create_session(
            session_type="implementation",
            repository="user/social-app",
            requirements=config["requirements"],
            dependencies=[sessions[dep]['session_id'] for dep in config["dependencies"] if dep in sessions]
        )
        sessions[component_name] = session
        
        # Start sessions with no dependencies immediately
        if not config["dependencies"]:
            await mcp_client.start_session(session['session_id'])
            print(f"🚀 Started {component_name} (priority {config['priority']})")
    
    return sessions


# Example of error handling and recovery
async def resilient_orchestration(mcp_client):
    """
    Shows how to handle failures and retry sessions
    """
    
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            session = await mcp_client.create_session(
                session_type="implementation",
                repository="user/project",
                requirements="Complex task that might fail"
            )
            
            await mcp_client.start_session(session['session_id'])
            
            # Monitor with shorter timeout
            result = await mcp_client.wait_for_session(
                session['session_id'],
                timeout_seconds=600,
                poll_interval_seconds=5
            )
            
            if result['status'] == 'completed':
                return result
            else:
                retry_count += 1
                print(f"⚠️  Session failed, retry {retry_count}/{max_retries}")
                
        except TimeoutError:
            retry_count += 1
            print(f"⏱️  Session timed out, retry {retry_count}/{max_retries}")
        
        except Exception as e:
            retry_count += 1
            print(f"❌ Error: {str(e)}, retry {retry_count}/{max_retries}")
    
    raise Exception("Max retries exceeded")


if __name__ == "__main__":
    # This would be run by Claude when orchestrating a project
    import asyncio
    
    # Example of how to use the orchestration
    async def main():
        # Initialize your MCP client here
        # mcp_client = YourMCPClient()
        
        # Run the orchestration
        # result = await orchestrate_todo_app(mcp_client)
        # print(json.dumps(result, indent=2))
        
        print("This is an example script showing orchestration patterns")
        print("In practice, Claude would use these patterns via MCP tools")
    
    asyncio.run(main())