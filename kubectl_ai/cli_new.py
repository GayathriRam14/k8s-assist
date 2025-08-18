#!/usr/bin/env python3
"""kubectl-ai CLI entry point"""

import sys
from rich.console import Console
from .interactive_cli_new import KubeAIAgentShell

console = Console()

def main():
    """Main entry point for kubectl-ai command"""
    try:
        # Check if we have command line arguments for one-shot mode
        if len(sys.argv) > 1:
            # One-shot mode - process single query and exit
            query = " ".join(sys.argv[1:])
            
            # Import here to avoid startup delay if modules missing
            try:
                from .main_agent import process_query
            except ImportError:
                try:
                    from .agentK8s import process_query
                    console.print("⚠️  Using legacy agentK8s")
                except ImportError:
                    console.print("[red]❌ Error: kubectl_ai modules not found[/red]")
                    sys.exit(1)
            
            # Process the query
            console.print(f"[bold blue]Query:[/bold blue] {query}")
            
            with console.status("[bold green]🧠 Processing..."):
                result = process_query(query)
            
            console.print("\n[bold green]Response:[/bold green]")
            console.print(result)
            
        else:
            # Interactive mode
            shell = KubeAIAgentShell()
            shell.cmdloop()
            
    except KeyboardInterrupt:
        console.print("\n[bold yellow]kubectl-ai interrupted[/bold yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]Fatal error:[/bold red] {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()