# Claude Orchestration MCP Server

An MCP (Model Context Protocol) server for orchestrating multiple Claude Code sessions to work on complex projects in parallel.

## Features

- Create and manage multiple Claude Code sessions
- Define dependencies between sessions
- Monitor session progress and status
- Retrieve session outputs
- Web-based interface using Gradio

## Setup

1. Install dependencies:
```bash
pip install gradio httpx python-dotenv
```

2. Configure environment variables:
   - Copy `.env.example` to `.env`
   - Update `CLAUDE_WEBHOOK_SECRET` with your actual webhook secret

3. Run the server:
```bash
./run_server.sh
# or
python mcp_server.py
```

The server will start at http://localhost:7860

## API Endpoints

The server exposes the following tools:

- **create_session**: Create a new Claude Code session
- **start_session**: Start a previously created session
- **get_session_status**: Check the status of a session
- **get_session_output**: Retrieve output from a completed session
- **list_sessions**: List all sessions with optional filtering
- **wait_for_session**: Wait for a session to complete

## Testing

Run the test script to verify your configuration:
```bash
python test_mcp_server.py
```

## Authentication

The server uses Bearer token authentication. Set your webhook secret in the `.env` file:
```
CLAUDE_WEBHOOK_SECRET=your-secret-here
```