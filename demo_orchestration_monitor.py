#!/usr/bin/env python3
"""
MCP Claude Hub - Orchestration Monitor
Real-time visualization of parallel Claude sessions
"""

import asyncio
import json
import os
import time
from datetime import datetime
from typing import Dict, List
import httpx
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

console = Console()

class SessionMonitor:
    def __init__(self):
        self.api_url = os.getenv("CLAUDE_HUB_API_URL", "https://claude.jonathanflatt.org/api/webhooks/claude")
        self.auth_token = os.getenv("CLAUDE_WEBHOOK_SECRET", "")
        self.sessions: Dict[str, dict] = {}
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def create_orchestration(self):
        """Create an orchestration with 4 parallel tasks"""
        payload = {
            "type": "orchestration.create",
            "orchestration": {
                "name": "Full-Stack Todo App Development",
                "description": "Building a complete todo application with parallel development",
                "repository": "Cheffromspace/demo-repository",
                "tasks": [
                    {
                        "type": "implementation",
                        "requirements": "Create React components for a todo list with TypeScript, Material-UI, and state management",
                        "dependencies": []
                    },
                    {
                        "type": "implementation", 
                        "requirements": "Build a FastAPI backend with SQLAlchemy for todo CRUD operations and PostgreSQL",
                        "dependencies": []
                    },
                    {
                        "type": "testing",
                        "requirements": "Write comprehensive pytest tests for all API endpoints with coverage > 90%",
                        "dependencies": ["backend"]  # Wait for backend to complete
                    },
                    {
                        "type": "documentation",
                        "requirements": "Generate OpenAPI documentation and README with setup instructions",
                        "dependencies": []
                    }
                ]
            }
        }
        
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
        
        response = await self.client.post(self.api_url, json=payload, headers=headers)
        return response.json()
    
    async def get_session_status(self, session_id: str):
        """Get status of a specific session"""
        payload = {
            "type": "session.get",
            "sessionId": session_id
        }
        
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
        
        response = await self.client.post(self.api_url, json=payload, headers=headers)
        data = response.json()
        
        if "results" in data and data["results"]:
            result = data["results"][0]
            if result.get("success"):
                return result.get("data", {}).get("session", {})
        return None
    
    def create_session_panel(self, session_id: str, session_data: dict) -> Panel:
        """Create a panel for a session"""
        status = session_data.get("status", "unknown")
        session_type = session_data.get("type", "unknown")
        project = session_data.get("project", {})
        
        # Status colors
        status_colors = {
            "pending": "yellow",
            "initializing": "cyan",
            "running": "green",
            "completed": "green bold",
            "failed": "red",
            "queued": "yellow"
        }
        
        # Create content
        content = []
        content.append(f"[bold]Type:[/bold] {session_type.upper()}")
        content.append(f"[bold]Status:[/bold] [{status_colors.get(status, 'white')}]{status}[/]")
        content.append("")
        content.append(f"[bold]Requirements:[/bold]")
        content.append(project.get("requirements", "N/A")[:100] + "...")
        
        # Add output if completed
        output = session_data.get("output", {})
        if output:
            content.append("")
            content.append("[bold]Output:[/bold]")
            if output.get("summary"):
                content.append(f"✓ {output['summary']}")
            if output.get("filesCreated"):
                content.append(f"✓ Created {len(output['filesCreated'])} files")
            if output.get("artifacts"):
                for artifact in output.get("artifacts", [])[:2]:
                    content.append(f"✓ {artifact}")
        
        # Progress indicator
        if status == "running":
            content.append("")
            content.append("[cyan]⣾[/] Working...")
        elif status == "completed":
            content.append("")
            content.append("[green]✓ Complete![/]")
        
        panel_title = f"Session {session_id[:8]}"
        panel_color = status_colors.get(status, "white")
        
        return Panel(
            "\n".join(content),
            title=panel_title,
            border_style=panel_color,
            expand=True
        )
    
    def create_dashboard(self) -> Layout:
        """Create the dashboard layout"""
        layout = Layout(name="root")
        
        # Create header
        header = Panel(
            Text.from_markup(
                "[bold cyan]MCP Claude Hub - Parallel Session Monitor[/]\n"
                "[yellow]Orchestrating Multiple Claude Sessions in Real-Time[/]",
                justify="center"
            ),
            style="cyan"
        )
        
        # Create main grid
        layout.split(
            Layout(header, size=4),
            Layout(name="main")
        )
        
        # Split main into 2x2 grid
        layout["main"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )
        
        layout["left"].split_column(
            Layout(name="session1"),
            Layout(name="session3")
        )
        
        layout["right"].split_column(
            Layout(name="session2"),
            Layout(name="session4")
        )
        
        # Add session panels
        session_ids = list(self.sessions.keys())
        for i, session_id in enumerate(session_ids[:4]):
            panel = self.create_session_panel(session_id, self.sessions[session_id])
            layout[f"session{i+1}"].update(panel)
        
        # Fill empty slots
        for i in range(len(session_ids), 4):
            layout[f"session{i+1}"].update(
                Panel("[dim]Waiting for session...[/]", border_style="dim")
            )
        
        return layout
    
    async def monitor_sessions(self):
        """Monitor sessions and update display"""
        console.clear()
        
        with Live(self.create_dashboard(), refresh_per_second=2) as live:
            # Create orchestration
            console.print("[yellow]Creating orchestration...[/]")
            orch_result = await self.create_orchestration()
            
            # Extract session IDs
            if "results" in orch_result and orch_result["results"]:
                for result in orch_result["results"]:
                    if result.get("success") and "sessions" in result.get("data", {}):
                        for session in result["data"]["sessions"]:
                            self.sessions[session["id"]] = session
            
            # Monitor until all complete
            while True:
                all_complete = True
                
                # Update each session
                for session_id in list(self.sessions.keys()):
                    session_data = await self.get_session_status(session_id)
                    if session_data:
                        self.sessions[session_id] = session_data
                        if session_data.get("status") not in ["completed", "failed"]:
                            all_complete = False
                
                # Update display
                live.update(self.create_dashboard())
                
                if all_complete:
                    break
                
                await asyncio.sleep(2)
        
        console.print("\n[green bold]All sessions complete![/]")

async def main():
    """Main entry point"""
    monitor = SessionMonitor()
    
    try:
        await monitor.monitor_sessions()
    except KeyboardInterrupt:
        console.print("\n[yellow]Monitoring stopped[/]")
    finally:
        await monitor.client.aclose()

if __name__ == "__main__":
    # Install rich if not available
    try:
        import rich
    except ImportError:
        os.system("pip install rich")
    
    asyncio.run(main())