# interactive_cli.py
import cmd
import readline
# from agent import process_query
from .agentK8s import process_query
from rich.console import Console
from rich.panel import Panel
import signal
import sys

console = Console()

class KubeAIAgentShell(cmd.Cmd):
    intro = "\n[bold cyan]Welcome to your K8s AI Agent 🧠[/bold cyan]\nType your question, or type 'exit' to quit."
    prompt = "[green]k8s-ai> [/green]"

    def preloop(self):
        signal.signal(signal.SIGINT, self.handle_sigint)
        self.history_file = ".k8s_ai_history"
        try:
            readline.read_history_file(self.history_file)
        except FileNotFoundError:
            pass

    def postloop(self):
        readline.write_history_file(self.history_file)

    def handle_sigint(self, signum, frame):
        console.print("\n[bold yellow]Use 'exit' to quit the shell.[/bold yellow]")
        self.cmdloop()

    def default(self, line):
        if line.lower() in ("exit", "quit"):
            return True

        console.print(Panel.fit(f"[bold white]Your Question:[/bold white] {line}", title="🤔 Query"))

        try:
            # result = process_query(line)
            result = process_query(line)
            console.print(Panel.fit(result, title="🧰 Response", style="cyan"))
        except Exception as e:
            console.print(Panel.fit(str(e), title="❌ Error", style="red"))

    def do_exit(self, arg):
        """Exit the shell."""
        console.print("[bold yellow]Goodbye![/bold yellow]")
        return True

if __name__ == '__main__':
    shell = KubeAIAgentShell()
    shell.cmdloop()
