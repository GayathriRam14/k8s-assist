# interactive_cli.py
import cmd
import readline
import signal
import sys
import os
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# Import the new modular kubectl_ai package
try:
    from .main_agent import process_query
    KUBECTL_AI_AVAILABLE = True
    print("✅ Using new modular kubectl_ai with Llama integration")
except ImportError:
    # Fallback to old import if new package not available
    try:
        from .agentK8s import process_query
        KUBECTL_AI_AVAILABLE = True
        print("⚠️  Using legacy agentK8s - consider upgrading to modular kubectl_ai")
    except ImportError:
        print("❌ Error: Neither kubectl_ai modules nor agentK8s found")
        KUBECTL_AI_AVAILABLE = False

console = Console()

class KubeAIAgentShell(cmd.Cmd):
    intro = """
╭─────────────────────────────────────────────────────────╮
│  🤖 Kubernetes AI Assistant v2.0                        │
│  💡 Powered by Llama + Expert Kubernetes Knowledge      │
│                                                         │
│  🔧 Natural Language → kubectl Commands → Smart Analysis │
╰─────────────────────────────────────────────────────────╯

[bold cyan]Welcome to your K8s AI Agent 🧠[/bold cyan]

[bold yellow]What I can help you with:[/bold yellow]
• 🔧 Troubleshoot pods, deployments, and services
• 🏥 Assess cluster health and identify issues  
• 📊 Analyze resource usage and performance
• 🖥️ Check node status and capacity
• 💡 Get actionable recommendations

[bold yellow]Example questions:[/bold yellow]
• "Why is my-pod crashing in staging?"
• "What pods are failing in the cluster?"
• "Show me node resource usage"
• "Check cluster health"
• "Which pods use most memory?"

[dim]Type your question, 'help' for more info, or 'exit' to quit.[/dim]
"""
    
    prompt = "[green]k8s-ai> [/green]"

    def preloop(self):
        signal.signal(signal.SIGINT, self.handle_sigint)
        self.history_file = ".k8s_ai_history"
        try:
            readline.read_history_file(self.history_file)
        except FileNotFoundError:
            pass
        
        # Check if kubectl_ai is available
        if not KUBECTL_AI_AVAILABLE:
            console.print("[red]❌ Error: kubectl_ai module not available[/red]")
            console.print("Please ensure the kubectl_ai package is properly installed.")

    def postloop(self):
        try:
            readline.write_history_file(self.history_file)
        except:
            pass  # Ignore errors when writing history

    def handle_sigint(self, signum, frame):
        console.print("\n[bold yellow]Use 'exit' to quit the shell.[/bold yellow]")
        console.print(f"{self.prompt}", end="")

    def default(self, line):
        """Handle user queries"""
        line = line.strip()
        
        # Handle exit commands
        if line.lower() in ("exit", "quit", "q", "bye"):
            return True
        
        # Handle empty input
        if not line:
            return False
        
        # Handle help command
        if line.lower() in ("help", "?", "h"):
            self.do_help("")
            return False
        
        # Handle clear command
        if line.lower() in ("clear", "cls"):
            os.system('cls' if os.name == 'nt' else 'clear')
            console.print(self.intro)
            return False

        # Display the user's query
        console.print(Panel.fit(f"[bold white]Your Question:[/bold white] {line}", title="🤔 Query"))

        # Check if kubectl_ai is available
        if not KUBECTL_AI_AVAILABLE:
            console.print(Panel.fit("[red]kubectl_ai module not available[/red]", title="❌ Error", style="red"))
            return False

        try:
            # Show processing indicator and process query
            with console.status("[bold green]🧠 Analyzing your query..."):
                result = process_query(line)
            
            # Display the response with your existing style
            console.print(Panel.fit(result, title="🧰 Response", style="cyan"))
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Query interrupted by user[/yellow]")
        except Exception as e:
            console.print(Panel.fit(f"[red]Error: {str(e)}[/red]\n\n[dim]Please check:\n• kubectl configuration\n• cluster connectivity\n• kubectl_ai module installation[/dim]", title="❌ Error", style="red"))

        return False

    def do_help(self, arg):
        """Show detailed help information"""
        help_text = """[bold cyan]🤖 Kubernetes AI Assistant Help[/bold cyan]

[bold yellow]What I can do:[/bold yellow]
• 🔧 Troubleshoot pods, deployments, and services
• 🏥 Assess cluster health and identify issues  
• 📊 Analyze resource usage and performance
• 🖥️ Check node status and capacity
• 💡 Provide actionable recommendations

[bold yellow]Example Questions:[/bold yellow]

[bold]🔧 Troubleshooting:[/bold]
• "Why is my-pod crashing in staging?"
• "Debug nginx deployment in production"
• "What's wrong with api-service?"
• "Why won't test pod start?"

[bold]🏥 Cluster Assessment:[/bold]
• "What issues does my cluster have?"
• "Check cluster health"
• "Any recommendations for improvements?"
• "What nodes have problems?"

[bold]📊 Resource Analysis:[/bold]
• "Which pods use most memory?"
• "Show me node resource usage"
• "Check resource usage in production"
• "What pods are consuming CPU?"

[bold]📋 Information Gathering:[/bold]
• "How many pods are running?"
• "List pods in staging namespace"
• "Show me all failing pods"
• "What namespaces exist?"

[bold yellow]Shell Commands:[/bold yellow]
• [cyan]help[/cyan] or [cyan]?[/cyan] - Show this help
• [cyan]clear[/cyan] - Clear the screen
• [cyan]exit[/cyan] or [cyan]quit[/cyan] - Exit the shell

[bold green]Features:[/bold green]
✅ Natural language understanding with Llama
✅ Automatic entity detection (pod names, namespaces)
✅ Smart troubleshooting workflows
✅ Safe read-only operations only
✅ Detailed analysis and recommendations
✅ Pattern detection for common issues

[bold blue]Tips:[/bold blue]
• Be specific about namespaces: "in staging namespace"
• Mention exact pod names when possible
• Ask about specific issues you're seeing
• Use natural language - I understand context!"""

        console.print(Panel.fit(help_text, title="📚 Help Guide", style="green"))

    def do_exit(self, arg):
        """Exit the shell."""
        console.print("[bold yellow]Goodbye! 👋[/bold yellow]")
        return True

    def do_quit(self, arg):
        """Exit the shell."""
        return self.do_exit(arg)

    def do_clear(self, arg):
        """Clear the screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
        console.print(self.intro)

if __name__ == '__main__':
    shell = KubeAIAgentShell()
    shell.cmdloop()