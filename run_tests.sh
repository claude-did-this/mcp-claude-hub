#!/bin/bash
# Simple test runner for Claude Orchestration MCP Server

echo "Running Claude Orchestration MCP Server Tests"
echo "============================================="
echo

# Run unit tests (no external dependencies)
echo "1. Running unit tests..."
python test_unit_simple.py
UNIT_RESULT=$?

echo
echo "2. Running smoke tests..."
# Only run smoke tests if we have auth configured
if [ -n "$CLAUDE_WEBHOOK_SECRET" ]; then
    python test_simple.py
    SMOKE_RESULT=$?
else
    echo "⚠️  Skipping smoke tests - CLAUDE_WEBHOOK_SECRET not set"
    SMOKE_RESULT=0
fi

echo
echo "============================================="
echo "Test Summary:"
echo "- Unit tests: $([ $UNIT_RESULT -eq 0 ] && echo '✅ PASSED' || echo '❌ FAILED')"
echo "- Smoke tests: $([ $SMOKE_RESULT -eq 0 ] && echo '✅ PASSED' || echo '❌ FAILED/SKIPPED')"
echo "============================================="

# Exit with error if any test failed
if [ $UNIT_RESULT -ne 0 ] || [ $SMOKE_RESULT -ne 0 ]; then
    exit 1
fi

exit 0