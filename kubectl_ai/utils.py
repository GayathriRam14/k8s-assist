# enhanced_utils.py
import subprocess
import json
import time
from typing import Dict, Any, Optional

class CommandCache:
    """Simple cache for kubectl command results to speed up repeated queries"""
    
    def __init__(self, ttl_seconds: int = 30):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl = ttl_seconds
    
    def get(self, command: str) -> Optional[str]:
        if command in self.cache:
            entry = self.cache[command]
            if time.time() - entry['timestamp'] < self.ttl:
                return entry['result']
            else:
                del self.cache[command]
        return None
    
    def set(self, command: str, result: str):
        self.cache[command] = {
            'result': result,
            'timestamp': time.time()
        }
    
    def clear(self):
        self.cache.clear()

# Global cache instance
cache = CommandCache()

def run_command(command: str, use_cache: bool = True) -> str:
    """Execute kubectl command with optional caching"""
    
    # Check cache first for read-only commands
    if use_cache and any(cmd in command for cmd in ['get', 'describe', 'logs']):
        cached_result = cache.get(command)
        if cached_result is not None:
            return f"{cached_result}\n\n[dim](cached result)[/dim]"
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=True,
            timeout=30
        )
        
        output = result.stdout
        
        # Cache the result for read-only commands
        if use_cache and any(cmd in command for cmd in ['get', 'describe', 'logs']):
            cache.set(command, output)
        
        return output
        
    except subprocess.TimeoutExpired:
        raise subprocess.CalledProcessError(1, command, "Command timed out after 30 seconds")
    except subprocess.CalledProcessError as e:
        # Include both stdout and stderr in error
        error_output = ""
        if e.stdout:
            error_output += f"STDOUT: {e.stdout}\n"
        if e.stderr:
            error_output += f"STDERR: {e.stderr}"
        
        raise subprocess.CalledProcessError(e.returncode, command, error_output.encode())

def parse_kubectl_output(output: str, resource_type: str) -> list:
    """Parse kubectl output into structured data"""
    lines = output.strip().split('\n')
    if len(lines) < 2:
        return []
    
    headers = lines[0].split()
    items = []
    
    for line in lines[1:]:
        if line.strip():
            values = line.split()
            if len(values) >= len(headers):
                item = dict(zip(headers, values))
                items.append(item)
    
    return items

def check_cluster_connectivity() -> bool:
    """Check if kubectl can connect to the cluster"""
    try:
        run_command("kubectl cluster-info --request-timeout=5s", use_cache=False)
        return True
    except subprocess.CalledProcessError:
        return False