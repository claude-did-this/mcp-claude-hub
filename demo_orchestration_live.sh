#!/bin/bash
# MCP Claude Hub - Ultimate Live Orchestration Demo
# Shows real-time execution with beautiful formatting

# Configuration
SSH_HOST="jonflatt@192.168.1.2"
REPO="Cheffromspace/demo-repository"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Colors
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Ensure parser is executable
chmod +x "$SCRIPT_DIR/demo_logs_parser.py"

# Kill existing sessions
tmux kill-session -t claude-live 2>/dev/null

clear
echo -e "${CYAN}${BOLD}"
echo "┌─────────────────────────────────────────────────────────────────┐"
echo "│                  MCP Claude Hub Live Demo                       │"
echo "│              Parallel AI Development in Action                  │"
echo "└─────────────────────────────────────────────────────────────────┘"
echo -e "${NC}"

# Step 1: Create orchestration
echo "🚀 Creating parallel development orchestration..."
echo ""

# Create a comprehensive project
ORCHESTRATION_CMD=$(cat << 'EOF'
Using the claude-hub MCP toolkit, create an orchestration called "E-Commerce API Development" with these parallel tasks:

1. Create a session to implement database models for products, users, and orders using TypeScript and Prisma
2. Create a session to build REST API endpoints for the e-commerce system using Express and TypeScript  
3. Create a session to implement authentication and authorization middleware
4. Create a session to write comprehensive test suites for all components

All in repository Cheffromspace/demo-repository
EOF
)

# Execute and capture session IDs
echo "Sending orchestration request..."
RESULT=$(claude --print "$ORCHESTRATION_CMD" 2>&1)

# Extract session IDs
SESSION_IDS=($(echo "$RESULT" | grep -oE '[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}' | head -4))

if [ ${#SESSION_IDS[@]} -lt 4 ]; then
    echo "❌ Failed to create sessions. Trying individual sessions..."
    
    # Fallback: Create individual sessions
    SESSION_IDS=()
    
    echo "Creating Models session..."
    ID=$(claude --print "Using claude-hub MCP toolkit, create a session to implement Prisma models for products, users, and orders in $REPO" 2>&1 | grep -oE '[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}' | head -1)
    SESSION_IDS+=("$ID")
    
    echo "Creating API session..."
    ID=$(claude --print "Using claude-hub MCP toolkit, create a session to build Express REST endpoints in $REPO" 2>&1 | grep -oE '[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}' | head -1)
    SESSION_IDS+=("$ID")
    
    echo "Creating Auth session..."
    ID=$(claude --print "Using claude-hub MCP toolkit, create a session to implement JWT authentication in $REPO" 2>&1 | grep -oE '[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}' | head -1)
    SESSION_IDS+=("$ID")
    
    echo "Creating Tests session..."
    ID=$(claude --print "Using claude-hub MCP toolkit, create a session to write Jest tests in $REPO" 2>&1 | grep -oE '[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}' | head -1)
    SESSION_IDS+=("$ID")
fi

echo ""
echo "✅ Created ${#SESSION_IDS[@]} parallel sessions!"
echo ""

# Map to container names
CONTAINERS=(
    "claude-implementation-${SESSION_IDS[0]:0:8}"
    "claude-implementation-${SESSION_IDS[1]:0:8}"
    "claude-implementation-${SESSION_IDS[2]:0:8}"
    "claude-testing-${SESSION_IDS[3]:0:8}"
)

# Worker details
WORKERS=(
    "🗄️  Database Models"
    "🌐 API Endpoints"
    "🔐 Authentication"
    "🧪 Test Suite"
)

COLORS=(green yellow cyan magenta)

# Step 2: Create tmux visualization
echo "📊 Setting up live monitoring dashboard..."
sleep 2

# Create tmux session
tmux new-session -d -s claude-live

# Create 2x2 layout
tmux split-window -v
tmux split-window -h
tmux select-pane -t 0
tmux split-window -h

# Setup each pane
for i in {0..3}; do
    tmux select-pane -t $i
    
    # Build the command to run
    if [ -f "$SCRIPT_DIR/demo_logs_parser.py" ]; then
        # Use parser for beautiful output
        CMD="ssh $SSH_HOST 'echo \"Waiting for ${CONTAINERS[$i]}...\"; "
        CMD+="while ! docker ps | grep -q ${CONTAINERS[$i]}; do sleep 0.5; done; "
        CMD+="docker logs -f ${CONTAINERS[$i]} 2>&1' | python3 $SCRIPT_DIR/demo_logs_parser.py '${WORKERS[$i]}' '${COLORS[$i]}'"
    else
        # Fallback to basic filtering
        CMD="ssh $SSH_HOST 'echo \"${WORKERS[$i]} - ${CONTAINERS[$i]}\"; "
        CMD+="echo \"════════════════════════════════════════\"; "
        CMD+="while ! docker ps | grep -q ${CONTAINERS[$i]}; do sleep 0.5; done; "
        CMD+="docker logs -f ${CONTAINERS[$i]} 2>&1 | grep -E \"(Writing:|Created:|Running:|✓|ERROR)\"'"
    fi
    
    tmux send-keys "$CMD" C-m
done

# Configure tmux appearance
tmux set -g status-style bg=colour234,fg=white
tmux set -g status-left "#[fg=cyan,bold] 🚀 Claude Orchestration "
tmux set -g status-right "#[fg=yellow] Sessions: ${#SESSION_IDS[@]} | %H:%M:%S"
tmux set -g status-interval 1
tmux set -g pane-border-style fg=colour240
tmux set -g pane-active-border-style fg=cyan

# Add monitoring pane at bottom
tmux select-layout tiled
tmux split-window -v -p 20
tmux select-pane -t 4

# Status monitoring command
STATUS_CMD="while true; do clear; "
STATUS_CMD+="echo -e '\\033[1;36m📊 Orchestration Status\\033[0m'; "
STATUS_CMD+="echo '═══════════════════════════════════════════════════════'; "
for i in {0..3}; do
    STATUS_CMD+="printf '%-20s: ' '${WORKERS[$i]}'; "
    STATUS_CMD+="ssh $SSH_HOST \"docker ps | grep -q ${CONTAINERS[$i]} && echo -e '\\033[32m● Running\\033[0m' || echo -e '\\033[33m○ Waiting\\033[0m'\"; "
done
STATUS_CMD+="echo ''; "
STATUS_CMD+="echo -e '\\033[33mTip: Use Ctrl+B then arrows to navigate panes\\033[0m'; "
STATUS_CMD+="sleep 2; done"

tmux send-keys "$STATUS_CMD" C-m

# Select first pane and attach
tmux select-pane -t 0

echo ""
echo "🎬 Launching live orchestration view..."
echo ""
sleep 1

# Attach to session
tmux attach-session -t claude-live