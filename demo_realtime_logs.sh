#!/bin/bash
# MCP Claude Hub - Real-time Docker Logs Visualization
# Shows streaming logs from parallel Claude containers in a 2x2 terminal split

# Colors and formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration
SSH_HOST="jonflatt@192.168.1.2"
DEMO_REPO="Cheffromspace/demo-repository"

# Check dependencies
if ! command -v tmux &> /dev/null; then
    echo "Installing tmux..."
    sudo apt-get update && sudo apt-get install -y tmux
fi

# Kill any existing demo session
tmux kill-session -t claude-logs-demo 2>/dev/null

echo -e "${CYAN}${BOLD}🚀 MCP Claude Hub - Real-time Parallel Execution Demo${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════════${NC}"
echo ""

# Create orchestration for demo
echo -e "${GREEN}Creating orchestration with 4 parallel tasks...${NC}"
ORCH_RESULT=$(claude --print "Using the claude-hub MCP toolkit, create 4 parallel sessions in ${DEMO_REPO}:
1. Implementation session: Create TypeScript models for a task management system
2. Implementation session: Build REST API controllers with Express
3. Testing session: Write unit tests for the models and controllers  
4. Documentation session: Generate API documentation and usage examples" 2>&1)

echo -e "${GREEN}Extracting session IDs...${NC}"
# Extract session IDs from the output
SESSION_IDS=($(echo "$ORCH_RESULT" | grep -oE '[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}' | head -4))

if [ ${#SESSION_IDS[@]} -lt 4 ]; then
    echo -e "${RED}Failed to create 4 sessions. Got: ${#SESSION_IDS[@]}${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Created ${#SESSION_IDS[@]} sessions${NC}"
echo ""

# Map session IDs to container names
declare -A CONTAINERS
CONTAINERS[0]="claude-implementation-${SESSION_IDS[0]:0:8}"  # Models
CONTAINERS[1]="claude-implementation-${SESSION_IDS[1]:0:8}"  # Controllers  
CONTAINERS[2]="claude-testing-${SESSION_IDS[2]:0:8}"         # Tests
CONTAINERS[3]="claude-documentation-${SESSION_IDS[3]:0:8}"   # Docs

# Task names for display
declare -A TASK_NAMES
TASK_NAMES[0]="📦 Models Worker"
TASK_NAMES[1]="🔧 Controllers Worker"
TASK_NAMES[2]="🧪 Testing Worker"
TASK_NAMES[3]="📚 Documentation Worker"

# Colors for each pane
declare -A PANE_COLORS
PANE_COLORS[0]=$GREEN
PANE_COLORS[1]=$YELLOW
PANE_COLORS[2]=$CYAN
PANE_COLORS[3]=$MAGENTA

# Create tmux session with 2x2 layout
echo -e "${BLUE}Setting up real-time monitoring dashboard...${NC}"
tmux new-session -d -s claude-logs-demo

# Split into 2x2 grid
tmux split-window -v
tmux split-window -h
tmux select-pane -t 0
tmux split-window -h

# Configure each pane to show filtered logs
for i in {0..3}; do
    tmux select-pane -t $i
    
    # Create the log streaming command with filtering
    LOG_CMD="ssh $SSH_HOST 'echo -e \"${PANE_COLORS[$i]}${BOLD}${TASK_NAMES[$i]}${NC}\"; "
    LOG_CMD+="echo -e \"${PANE_COLORS[$i]}Container: ${CONTAINERS[$i]}${NC}\"; "
    LOG_CMD+="echo -e \"${PANE_COLORS[$i]}════════════════════════════════════════${NC}\"; "
    LOG_CMD+="echo \"\"; "
    
    # Wait for container to exist then follow logs with formatting
    LOG_CMD+="while ! docker ps -a | grep -q ${CONTAINERS[$i]}; do sleep 1; done; "
    LOG_CMD+="docker logs -f ${CONTAINERS[$i]} 2>&1 | while IFS= read -r line; do "
    LOG_CMD+="  if echo \"\$line\" | grep -q \"type.*:.*tool_use\"; then "
    LOG_CMD+="    tool=\$(echo \"\$line\" | grep -oE \"name.*:.*\\\"[^\\\"]+\\\"\" | sed \"s/.*\\\"\\([^\\\"]*\\)\\\".*/\\1/\"); "
    LOG_CMD+="    echo -e \"${PANE_COLORS[$i]}⚡ Using tool: \$tool${NC}\"; "
    LOG_CMD+="  elif echo \"\$line\" | grep -q \"File.*successfully\"; then "
    LOG_CMD+="    file=\$(echo \"\$line\" | grep -oE \"/[^\\\"]+\" | head -1); "
    LOG_CMD+="    echo -e \"${PANE_COLORS[$i]}✓ Created: \$file${NC}\"; "
    LOG_CMD+="  elif echo \"\$line\" | grep -q \"test.*passed\"; then "
    LOG_CMD+="    echo -e \"${PANE_COLORS[$i]}✓ Tests passing${NC}\"; "
    LOG_CMD+="  elif echo \"\$line\" | grep -q \"Analyzing\\|Scanning\\|Processing\"; then "
    LOG_CMD+="    echo -e \"${PANE_COLORS[$i]}⟳ \$line${NC}\"; "
    LOG_CMD+="  elif echo \"\$line\" | grep -q \"ERROR\"; then "
    LOG_CMD+="    echo -e \"${RED}❌ Error detected${NC}\"; "
    LOG_CMD+="  elif echo \"\$line\" | grep -q \"result.*:.*success\"; then "
    LOG_CMD+="    echo -e \"${PANE_COLORS[$i]}${BOLD}✓ Task completed!${NC}\"; "
    LOG_CMD+="  fi; "
    LOG_CMD+="done'"
    
    tmux send-keys "$LOG_CMD" C-m
done

# Add status bar
tmux set -g status-style bg=black,fg=white
tmux set -g status-left "#[fg=cyan,bold] Claude Orchestration "
tmux set -g status-right "#[fg=yellow] %H:%M:%S"
tmux set -g status-interval 1

# Instructions overlay (will clear after a few seconds)
tmux select-pane -t 0
echo ""
echo -e "${CYAN}${BOLD}┌─────────────────────────────────────────────────────────────┐${NC}"
echo -e "${CYAN}${BOLD}│          Real-time Parallel Claude Execution                │${NC}"
echo -e "${CYAN}${BOLD}├─────────────────────────┬───────────────────────────────────┤${NC}"
echo -e "${CYAN}${BOLD}│ ${GREEN}Models Worker${CYAN}          │ ${YELLOW}Controllers Worker${CYAN}              │${NC}"
echo -e "${CYAN}${BOLD}│ Creating TypeScript     │ Building REST endpoints         │${NC}"
echo -e "${CYAN}${BOLD}├─────────────────────────┼───────────────────────────────────┤${NC}"
echo -e "${CYAN}${BOLD}│ ${CYAN}Testing Worker${CYAN}         │ ${MAGENTA}Documentation Worker${CYAN}            │${NC}"
echo -e "${CYAN}${BOLD}│ Writing unit tests      │ Generating API docs             │${NC}"
echo -e "${CYAN}${BOLD}└─────────────────────────┴───────────────────────────────────┘${NC}"
echo ""
echo -e "${YELLOW}Controls: Ctrl+B then arrows to navigate | Ctrl+B then D to detach${NC}"
echo -e "${GREEN}Launching in 3 seconds...${NC}"

sleep 3

# Attach to the session
tmux attach-session -t claude-logs-demo