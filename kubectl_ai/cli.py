#!/usr/bin/env python3
"""kubectl-ai CLI entry point"""

import sys
from rich.console import Console
from .interactive_cli import KubeAIAgentShell  # Use your actual class name

console = Console()

def main():
    """Main entry point for kubectl-ai command"""
    try:
        shell = KubeAIAgentShell()  # Your actual class name
        shell.cmdloop()
    except KeyboardInterrupt:
        console.print("\n[bold yellow]kubectl-ai interrupted[/bold yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]Fatal error:[/bold red] {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()