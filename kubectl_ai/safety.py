# safety.py - Safety and command validation

SAFE_COMMANDS = [
    "kubectl get",
    "kubectl describe",
    "kubectl logs",
    "kubectl top",
    "kubectl explain",
    "kubectl version",
    "kubectl cluster-info"
]

BLOCKED_COMMANDS = ["delete", "apply", "create", "edit", "patch", "replace", "scale"]

# Invalid flags that Llama sometimes generates
INVALID_FLAGS = ["--since", "--recent", "--last", "--time", "--ago", "--before", "--after"]

def is_safe_command(cmd: str) -> bool:
    """Check if a kubectl command is safe (read-only) and uses valid flags"""
    if any(bad in cmd.lower() for bad in BLOCKED_COMMANDS):
        return False
    
    if not any(cmd.strip().startswith(good) for good in SAFE_COMMANDS):
        return False
    
    # Check for invalid flags
    if any(flag in cmd for flag in INVALID_FLAGS):
        print(f"Warning: Command contains invalid flag: {cmd}")
        return False
    
    return True