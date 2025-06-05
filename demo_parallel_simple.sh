#!/bin/bash
# MCP Claude Hub - Simple Parallel Demo
# Shows 4 sessions being created and monitored

echo "🚀 MCP Claude Hub - Parallel Session Demo"
echo "========================================="
echo ""

# Create 4 sessions in parallel
echo "📦 Creating 4 parallel sessions..."
echo ""

# Session 1: Frontend
echo "1️⃣ Frontend Session:"
SESSION1=$(claude --print "Using the claude-hub MCP toolkit, create a session to build a React todo list component in Cheffromspace/demo-repository" 2>&1 | grep -oE '[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}' | head -1)
echo "   Session ID: $SESSION1"

# Session 2: Backend  
echo "2️⃣ Backend Session:"
SESSION2=$(claude --print "Using the claude-hub MCP toolkit, create a session to build a FastAPI backend for todos in Cheffromspace/demo-repository" 2>&1 | grep -oE '[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}' | head -1)
echo "   Session ID: $SESSION2"

# Session 3: Tests
echo "3️⃣ Testing Session:"
SESSION3=$(claude --print "Using the claude-hub MCP toolkit, create a session to write tests for the todo API in Cheffromspace/demo-repository" 2>&1 | grep -oE '[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}' | head -1)
echo "   Session ID: $SESSION3"

# Session 4: Docs
echo "4️⃣ Documentation Session:"
SESSION4=$(claude --print "Using the claude-hub MCP toolkit, create a session to create API documentation in Cheffromspace/demo-repository" 2>&1 | grep -oE '[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}' | head -1)
echo "   Session ID: $SESSION4"

echo ""
echo "✅ All sessions created! Monitoring progress..."
echo ""

# Monitor sessions
check_session() {
    local session_id=$1
    local session_name=$2
    local status=$(claude --print "Using the claude-hub MCP toolkit, get the status of session $session_id" 2>&1 | grep -oE 'Status: \w+' | cut -d' ' -f2)
    echo "$session_name: $status"
}

# Monitor loop
while true; do
    echo -ne "\033[4A" # Move cursor up 4 lines
    check_session "$SESSION1" "1️⃣ Frontend  "
    check_session "$SESSION2" "2️⃣ Backend   "
    check_session "$SESSION3" "3️⃣ Tests     "
    check_session "$SESSION4" "4️⃣ Docs      "
    
    # Check if all are complete
    if [[ $(check_session "$SESSION1" "1") =~ "completed" ]] && \
       [[ $(check_session "$SESSION2" "2") =~ "completed" ]] && \
       [[ $(check_session "$SESSION3" "3") =~ "completed" ]] && \
       [[ $(check_session "$SESSION4" "4") =~ "completed" ]]; then
        echo ""
        echo "🎉 All sessions completed successfully!"
        break
    fi
    
    sleep 5
done