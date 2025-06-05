#!/usr/bin/env python3
"""
Real-time log parser for Claude containers
Provides beautiful visualization of parallel execution
"""

import json
import re
import sys
from datetime import datetime
from typing import Dict, Optional

# ANSI color codes
COLORS = {
    'red': '\033[91m',
    'green': '\033[92m',
    'yellow': '\033[93m',
    'blue': '\033[94m',
    'magenta': '\033[95m',
    'cyan': '\033[96m',
    'white': '\033[97m',
    'bold': '\033[1m',
    'reset': '\033[0m',
    'dim': '\033[2m'
}

class ClaudeLogParser:
    def __init__(self, worker_name: str, color: str = 'white'):
        self.worker_name = worker_name
        self.color = COLORS.get(color, COLORS['white'])
        self.current_tool = None
        self.files_created = []
        self.files_modified = []
        self.tests_run = 0
        self.tests_passed = 0
        
    def parse_line(self, line: str) -> Optional[str]:
        """Parse a log line and return formatted output"""
        try:
            # Try to parse as JSON
            if line.strip().startswith('{'):
                data = json.loads(line)
                return self.parse_json_log(data)
        except:
            # Fall back to text parsing
            return self.parse_text_log(line)
    
    def parse_json_log(self, data: Dict) -> Optional[str]:
        """Parse JSON structured logs"""
        msg_type = data.get('type', '')
        
        if msg_type == 'user' and 'tool_result' in str(data):
            # Tool result
            content = data.get('message', {}).get('content', [])
            if content and isinstance(content[0], dict):
                result = content[0].get('content', '')
                if 'created successfully' in result:
                    file_match = re.search(r'at: (.+)$', result)
                    if file_match:
                        filename = file_match.group(1)
                        self.files_created.append(filename)
                        return f"{self.color}✓ Created: {filename}{COLORS['reset']}"
                elif 'updated' in result:
                    return f"{self.color}✓ Updated file{COLORS['reset']}"
                elif 'Tool ran without output' in result:
                    return f"{self.color}✓ Command executed{COLORS['reset']}"
        
        elif msg_type == 'assistant':
            # Claude's actions
            message = data.get('message', {})
            if 'content' in message:
                for content in message.get('content', []):
                    if content.get('type') == 'tool_use':
                        tool_name = content.get('name', 'unknown')
                        self.current_tool = tool_name
                        
                        # Format based on tool
                        if tool_name == 'Write':
                            inp = content.get('input', {})
                            file_path = inp.get('file_path', '')
                            return f"{self.color}📝 Writing: {file_path}{COLORS['reset']}"
                        elif tool_name == 'Read':
                            inp = content.get('input', {})
                            file_path = inp.get('file_path', '')
                            return f"{self.color}👁️  Reading: {file_path}{COLORS['reset']}"
                        elif tool_name == 'Bash':
                            inp = content.get('input', {})
                            cmd = inp.get('command', '')[:50]
                            return f"{self.color}⚡ Running: {cmd}...{COLORS['reset']}"
                        elif tool_name == 'TodoWrite':
                            return f"{self.color}📋 Updating task list{COLORS['reset']}"
                        else:
                            return f"{self.color}🔧 Using: {tool_name}{COLORS['reset']}"
                    
                    elif content.get('type') == 'text':
                        text = content.get('text', '')
                        # Extract key phrases
                        if 'test' in text.lower() and 'pass' in text.lower():
                            self.tests_passed += 1
                            return f"{self.color}✅ Tests passing!{COLORS['reset']}"
                        elif 'created' in text.lower() and 'successfully' in text.lower():
                            return f"{self.color}✓ Task completed{COLORS['reset']}"
        
        elif 'result' in data:
            # Session result
            result = data.get('result', '')
            if 'Created PR' in result or 'pull request' in result.lower():
                pr_match = re.search(r'#(\d+)', result)
                if pr_match:
                    pr_num = pr_match.group(1)
                    return f"{COLORS['bold']}{self.color}🎉 Created PR #{pr_num}!{COLORS['reset']}"
        
        return None
    
    def parse_text_log(self, line: str) -> Optional[str]:
        """Parse plain text logs"""
        # Skip empty lines
        if not line.strip():
            return None
        
        # ERROR lines
        if 'ERROR' in line:
            if 'OAuth token has expired' in line:
                return f"{COLORS['yellow']}⚠️  Auth token expired (non-critical){COLORS['reset']}"
            else:
                return f"{COLORS['red']}❌ Error: {line.strip()}{COLORS['reset']}"
        
        # Progress indicators
        if any(word in line.lower() for word in ['analyzing', 'scanning', 'processing', 'building']):
            return f"{self.color}⟳ {line.strip()}{COLORS['reset']}"
        
        # Success indicators
        if any(word in line.lower() for word in ['complete', 'success', 'done', 'finished']):
            return f"{COLORS['bold']}{self.color}✓ {line.strip()}{COLORS['reset']}"
        
        # File operations
        if 'created' in line.lower() or 'modified' in line.lower():
            return f"{self.color}📄 {line.strip()}{COLORS['reset']}"
        
        return None
    
    def get_summary(self) -> str:
        """Get execution summary"""
        summary = f"\n{COLORS['bold']}{self.color}═══ {self.worker_name} Summary ═══{COLORS['reset']}\n"
        if self.files_created:
            summary += f"{self.color}Files created: {len(self.files_created)}{COLORS['reset']}\n"
            for f in self.files_created[-3:]:  # Show last 3
                summary += f"  - {f}\n"
        if self.tests_passed:
            summary += f"{self.color}Tests passed: {self.tests_passed}{COLORS['reset']}\n"
        return summary

def main():
    """Main entry point for log parsing"""
    if len(sys.argv) < 3:
        print("Usage: demo_logs_parser.py <worker_name> <color>")
        sys.exit(1)
    
    worker_name = sys.argv[1]
    color = sys.argv[2]
    
    parser = ClaudeLogParser(worker_name, color)
    
    # Print header
    print(f"{COLORS['bold']}{COLORS[color]}{'═' * 50}{COLORS['reset']}")
    print(f"{COLORS['bold']}{COLORS[color]}{worker_name:^50}{COLORS['reset']}")
    print(f"{COLORS['bold']}{COLORS[color]}{'═' * 50}{COLORS['reset']}")
    print()
    
    try:
        # Read from stdin (piped from docker logs)
        for line in sys.stdin:
            formatted = parser.parse_line(line)
            if formatted:
                print(formatted)
                sys.stdout.flush()
    except KeyboardInterrupt:
        # Print summary on exit
        print(parser.get_summary())

if __name__ == "__main__":
    main()