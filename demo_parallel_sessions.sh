#!/bin/bash
# MCP Claude Hub - Parallel Sessions Demo
# Shows 4 Claude sessions working in parallel in a 2x2 terminal split

# Colors for better visual effect
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Check if tmux is installed
if ! command -v tmux &> /dev/null; then
    echo "Installing tmux for terminal splitting..."
    sudo apt-get update && sudo apt-get install -y tmux
fi

# Kill any existing demo session
tmux kill-session -t mcp-demo 2>/dev/null

# Create a new tmux session with 2x2 layout
echo -e "${BLUE}Setting up 2x2 terminal split for parallel Claude sessions...${NC}"
tmux new-session -d -s mcp-demo

# Split into 2x2 grid
tmux split-window -v
tmux split-window -h
tmux select-pane -t 0
tmux split-window -h

# Session 1: Frontend Implementation (Top Left)
tmux select-pane -t 0
tmux send-keys "echo -e '${GREEN}SESSION 1: Frontend Implementation${NC}'" C-m
tmux send-keys "echo 'Creating React components for demo app...'" C-m
tmux send-keys "sleep 2" C-m
tmux send-keys "claude --print 'Using the claude-hub MCP toolkit, create a session to implement a React frontend component for a todo list with TypeScript in Cheffromspace/demo-repository'" C-m

# Session 2: Backend API (Top Right)
tmux select-pane -t 1
tmux send-keys "echo -e '${YELLOW}SESSION 2: Backend API${NC}'" C-m
tmux send-keys "echo 'Building REST API endpoints...'" C-m
tmux send-keys "sleep 3" C-m
tmux send-keys "claude --print 'Using the claude-hub MCP toolkit, create a session to implement a Python FastAPI backend with CRUD operations for todos in Cheffromspace/demo-repository'" C-m

# Session 3: Testing Suite (Bottom Left)
tmux select-pane -t 2
tmux send-keys "echo -e '${RED}SESSION 3: Testing Suite${NC}'" C-m
tmux send-keys "echo 'Writing comprehensive tests...'" C-m
tmux send-keys "sleep 4" C-m
tmux send-keys "claude --print 'Using the claude-hub MCP toolkit, create a session to write pytest tests for the todo API endpoints in Cheffromspace/demo-repository'" C-m

# Session 4: Documentation (Bottom Right)
tmux select-pane -t 3
tmux send-keys "echo -e '${BLUE}SESSION 4: Documentation${NC}'" C-m
tmux send-keys "echo 'Generating API documentation...'" C-m
tmux send-keys "sleep 5" C-m
tmux send-keys "claude --print 'Using the claude-hub MCP toolkit, create a session to generate comprehensive API documentation with examples in Cheffromspace/demo-repository'" C-m

# Attach to the session
echo -e "${GREEN}Launching parallel sessions demo...${NC}"
echo -e "${YELLOW}Press Ctrl+B then D to detach from the session${NC}"
echo -e "${YELLOW}Press Ctrl+B then arrow keys to navigate between panes${NC}"
sleep 2
tmux attach-session -t mcp-demo