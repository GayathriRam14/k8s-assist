# """kubectl-ai: Intelligent Kubernetes Assistant"""
# __version__ = "1.0.0"
# __init__.py - Package initialization with safe imports

# Import core functions with error handling
try:
    from .main_agent import process_query
    MAIN_AGENT_AVAILABLE = True
except ImportError as e:
    print(f"Warning: main_agent import failed: {e}")
    MAIN_AGENT_AVAILABLE = False
    # Fallback to legacy agent if available
    try:
        from .agentK8s import process_query
        print("Using legacy agentK8s as fallback")
    except ImportError:
        print("No process_query function available")
        process_query = None

# Import other modules with error handling
try:
    from .entity_extraction import extract_entities, requires_pod_context
except ImportError as e:
    print(f"Warning: entity_extraction import failed: {e}")
    extract_entities = None
    requires_pod_context = None

try:
    from .query_detection import detect_query_type, detect_troubleshooting_intent
except ImportError as e:
    print(f"Warning: query_detection import failed: {e}")
    detect_query_type = None
    detect_troubleshooting_intent = None

try:
    from .safety import is_safe_command
except ImportError as e:
    print(f"Warning: safety import failed: {e}")
    is_safe_command = None

try:
    from .workflows import TROUBLESHOOTING_WORKFLOWS
except ImportError as e:
    print(f"Warning: workflows import failed: {e}")
    TROUBLESHOOTING_WORKFLOWS = {}

# Define what's available for import
__all__ = []
if process_query:
    __all__.append('process_query')
if extract_entities:
    __all__.extend(['extract_entities', 'requires_pod_context'])
if detect_query_type:
    __all__.extend(['detect_query_type', 'detect_troubleshooting_intent'])
if is_safe_command:
    __all__.append('is_safe_command')
if TROUBLESHOOTING_WORKFLOWS:
    __all__.append('TROUBLESHOOTING_WORKFLOWS')