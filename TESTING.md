# Testing Guide

## Quick Start

Run all tests:
```bash
./run_tests.sh
```

## Test Files

1. **test_unit_simple.py** - Basic unit tests that don't require external dependencies
   - Tests initialization
   - Tests payload structures
   - Tests session types
   - No API calls required

2. **test_simple.py** - Smoke tests that make real API calls
   - Tests create session
   - Tests list sessions
   - Tests get session status
   - Requires `CLAUDE_WEBHOOK_SECRET` environment variable

3. **test_mcp_server.py** - Full integration tests (original)
   - Comprehensive API testing
   - Detailed output
   - Requires authentication

## Running Individual Tests

```bash
# Unit tests only (no API required)
python test_unit_simple.py

# Smoke tests (requires API)
python test_simple.py

# Full integration tests
python test_mcp_server.py
```

## CI/CD

GitHub Actions runs unit tests automatically on push/PR. Smoke tests are skipped in CI as they require API access.

## Environment Variables

For API tests, set:
```bash
export CLAUDE_WEBHOOK_SECRET="your-secret-here"
export CLAUDE_HUB_API_URL="https://your-api-url/api/webhooks/claude"  # optional
```