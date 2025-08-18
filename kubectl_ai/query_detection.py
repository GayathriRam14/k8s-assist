# query_detection.py - Query type and intent detection

def detect_query_type(prompt: str) -> str:
    """Detect the type of query to determine response strategy"""
    prompt_lower = prompt.lower().strip()
    
    # Check for assessment/troubleshooting keywords first (higher priority)
    assessment_keywords = [
        'issues', 'problems', 'failing', 'failed', 'error', 'errors',
        'broken', 'unhealthy', 'not ready', 'trouble', 'wrong'
    ]
    
    # If asking about nodes WITH issues/problems, it's assessment not simple info
    if 'node' in prompt_lower and any(keyword in prompt_lower for keyword in assessment_keywords):
        return 'assessment'
    
    # Cluster-level informational queries - simple info only
    simple_cluster_queries = [
        'list nodes', 'show nodes', 'get nodes',
        'how many namespaces', 'list namespaces', 'show namespaces',
        'what taints', 'show taints', 'node taints', 'taint',
        'what labels', 'node labels', 'show labels',
        'storage class', 'storageclass', 'sc',
        'persistent volume', 'pv', 'pvc',
        'ingress', 'network policy', 'rbac'
    ]
    
    # Only match "how many nodes" if it's NOT asking about issues
    if 'how many nodes' in prompt_lower and not any(keyword in prompt_lower for keyword in assessment_keywords):
        return 'cluster_info'
    
    if any(query in prompt_lower for query in simple_cluster_queries):
        return 'cluster_info'
    
    # Resource management queries - MORE SPECIFIC
    if any(pattern in prompt_lower for pattern in [
        'which pods use most', 'what pods use most', 'pods that use most',
        'highest memory', 'highest cpu', 'most memory', 'most cpu',
        'top memory', 'top cpu', 'pod uses highest', 'pod using most',
        'resource usage', 'memory usage', 'cpu usage', 'performance', 'top pods'
    ]) or ('check' in prompt_lower and any(word in prompt_lower for word in ['resource', 'memory', 'cpu', 'usage', 'performance'])):
        return 'resource'
    
    # Node performance queries
    if any(word in prompt_lower for word in ['node performance', 'show me node', 'node resource', 'node usage']):
        return 'resource'
    
    # Conversational/greeting patterns
    greeting_patterns = [
        'hello', 'hi there', 'hey there', 'good morning', 'good afternoon', 'good evening',
        'howdy', 'greetings'
    ]
    
    if (prompt_lower in greeting_patterns or 
        prompt_lower in ['hi', 'hey', 'hello there', "what's up", 'whats up', 'sup']):
        return 'greeting'
    
    help_patterns = [
        'help', 'what can you do', 'what do you do', 'how do you work',
        'what are your capabilities', 'commands', 'examples', 'usage',
        'how to use', 'guide', 'tutorial', 'what questions'
    ]
    
    goodbye_patterns = [
        'bye', 'goodbye', 'see you', 'thanks', 'thank you', 'exit', 'quit'
    ]
    
    if any(pattern in prompt_lower for pattern in help_patterns):
        return 'help'
    
    if any(pattern in prompt_lower for pattern in goodbye_patterns):
        return 'goodbye'
    
    # Troubleshooting queries - expanded patterns
    pod_troubleshooting_patterns = [
        'debug pod', 'pod failing', 'pod crashed', 'pod crash', 'pod crashing', 
        'pod crash loop', 'pod not running', 'pod pending', 'pod stuck', 
        'pod not starting', 'pod wont start', 'pod error', 'pod issue',
        'debug failpod', 'why is pod', 'troubleshoot pod',
        "won't start", "wont start", "not starting", "why won't",
        "why wont", "start in", "failing in", "crashing in"
    ]
    
    if any(pattern in prompt_lower for pattern in pod_troubleshooting_patterns):
        return 'troubleshooting'
    
    # General troubleshooting - catch more patterns
    troubleshoot_indicators = ['failing', 'crashed', 'crash', 'crashing', 'stuck', 'pending', 'error']
    context_indicators = ['pod', 'container', 'deployment', 'service']
    
    if (any(word in prompt_lower for word in troubleshoot_indicators) and 
        any(word in prompt_lower for word in context_indicators)):
        return 'troubleshooting'
    
    # Pattern: "why won't X start" or "X won't start"
    if any(pattern in prompt_lower for pattern in ["won't start", "wont start", "not starting"]):
        return 'troubleshooting'
    
    # Cluster assessment queries - expanded to catch node issues
    assessment_patterns = [
        'improve', 'health', 'assessment', 'issues', 'problems', 'optimize',
        'recommendations', 'best practices', 'cluster status', 'overall',
        'anything wrong', 'check cluster', 'audit', 'need to improve',
        'improvements', 'what should i', 'areas for improvement',
        'cluster health', 'performance issues', 'bottlenecks',
        'nodes have issues', 'nodes with problems', 'problematic nodes',
        'unhealthy nodes', 'failing nodes', 'broken nodes', 'node issues'
    ]
    
    if any(pattern in prompt_lower for pattern in assessment_patterns):
        return 'assessment'
    
    # Simple informational queries about pods and deployments
    if any(pattern in prompt_lower for pattern in [
        'how many pods', 'list pods', 'show me pods', 'get all pods', 'what pods', 'which pods',
        'count pods', 'total pods', 'pod overview', 'pod status',
        'how many deployments', 'list deployments', 'show me deployments', 'get all deployments', 
        'what deployments', 'which deployments', 'recent deployments', 'deployment overview'
    ]):
        return 'informational'
    
    # General informational queries (non-pod specific)  
    if any(pattern in prompt_lower for pattern in [
        'how many', 'list', 'show me', 'get all', 'count', 'total', 'overview', 'status of'
    ]):
        return 'cluster_info'
    
    # Date-specific deployment queries - EXPANDED
    if any(term in prompt_lower for term in ['deployed', 'deployment', 'deployments']) and any(date_term in prompt_lower for date_term in [
        'august', 'september', 'october', 'november', 'december', 'january', 'february', 'march', 'april', 'may', 'june', 'july',
        '18th', '19th', '20th', '21st', '22nd', '23rd', '24th', '25th', '2024', '2025',
        'yesterday', 'today', 'last week', 'this week', 'last month', 'this month'
    ]):
        return 'cluster_info'
    
    # Time-based deployment queries - EXPANDED
    if any(term in prompt_lower for term in ['deployed', 'deployment', 'deployments']) and any(time_term in prompt_lower for time_term in [
        '24 hours', 'last day', 'today', 'recent', 'last', 'yesterday', 'from yesterday',
        'past hour', 'past day', 'past week', 'this morning', 'this afternoon'
    ]):
        return 'cluster_info'
    
    # Event queries with dates
    if any(term in prompt_lower for term in ['events', 'event']) and any(date_term in prompt_lower for date_term in [
        'august', 'september', 'october', 'november', 'december', 'january', 'february', 'march', 'april', 'may', 'june', 'july',
        '1st', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th', '10th', '11th', '12th', '13th', '14th', '15th', '16th', '17th', '18th', '19th', '20th', '21st', '22nd', '23rd', '24th', '25th', '26th', '27th', '28th', '29th', '30th', '31st',
        '2024', '2025', 'yesterday', 'today', 'last week', 'this week', 'last month', 'this month'
    ]):
        return 'cluster_info'
    
    # Event queries
    if any(term in prompt_lower for term in ['events', 'event', 'cluster events', 'get events']):
        return 'cluster_info'
    
    return 'general'

def detect_troubleshooting_intent(prompt: str) -> str:
    """Detect what kind of troubleshooting the user wants"""
    prompt_lower = prompt.lower()
    
    # Check for node-specific issues first
    if any(pattern in prompt_lower for pattern in [
        'nodes have issues', 'nodes with problems', 'node issues', 'nodes issues',
        'problematic nodes', 'unhealthy nodes', 'failing nodes', 'broken nodes',
        'how many nodes', 'which nodes'
    ]) and any(keyword in prompt_lower for keyword in ['issues', 'problems', 'failing', 'broken', 'unhealthy']):
        return 'node_assessment'
    
    # Check for cluster-wide failing pods queries
    if any(pattern in prompt_lower for pattern in [
        'what pods are failing', 'which pods are failing', 'pods failing', 
        'failed pods', 'broken pods', 'failing in the cluster', 'failing in cluster'
    ]) or ('cluster' in prompt_lower and any(word in prompt_lower for word in ['failing', 'failed', 'broken'])):
        return 'failing_pods_cluster'
    
    # Check for "won't start" or "not starting" patterns - treat as pod_not_running
    if any(pattern in prompt_lower for pattern in ["won't start", "wont start", "not starting", "not start"]):
        return 'pod_not_running'
    
    if any(word in prompt_lower for word in ['failing', 'crashed', 'crash', 'restart', 'crashing', 'crash loop']):
        return 'pod_crashing'
    elif any(word in prompt_lower for word in ['not running', 'pending', 'stuck', 'not starting', 'wont start']):
        return 'pod_not_running'
    elif any(word in prompt_lower for word in ['service', 'connection', 'network', 'endpoint']):
        return 'service_issues'
    elif any(word in prompt_lower for word in ['deployment', 'replica', 'scaling']):
        return 'deployment_issues'
    elif any(word in prompt_lower for word in ['resource', 'memory', 'cpu', 'usage', 'performance']):
        return 'resource_usage'
    
    return None

def generate_cluster_info_commands(prompt: str) -> list:
    """Generate commands for cluster-level information queries"""
    prompt_lower = prompt.lower()
    
def generate_cluster_info_commands(prompt: str) -> list:
    """Generate commands for cluster-level information queries"""
    prompt_lower = prompt.lower()
    
    # Handle event queries with dates
    if any(term in prompt_lower for term in ['events', 'event']) and any(date_term in prompt_lower for date_term in [
        'august', 'september', 'october', 'november', 'december', 'january', 'february', 'march', 'april', 'may', 'june', 'july',
        '1st', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th', '10th', '11th', '12th', '13th', '14th', '15th', '16th', '17th', '18th', '19th', '20th', '21st', '22nd', '23rd', '24th', '25th', '26th', '27th', '28th', '29th', '30th', '31st',
        '2024', '2025', 'yesterday', 'today', 'last week', 'this week', 'last month', 'this month'
    ]):
        return [
            "kubectl get events --all-namespaces --sort-by='.firstTimestamp'",
            "kubectl get events --all-namespaces -o jsonpath='{range .items[*]}{.metadata.name}{\"\\t\"}{.metadata.namespace}{\"\\t\"}{.firstTimestamp}{\"\\t\"}{.reason}{\"\\t\"}{.message}{\"\\n\"}{end}'"
        ]
    
    # Handle all date/time-specific deployment queries with exact timestamps
    elif any(term in prompt_lower for term in ['deployed', 'deployment', 'deployments']) and any(date_term in prompt_lower for date_term in [
        'august', 'september', 'october', 'november', 'december', 'january', 'february', 'march', 'april', 'may', 'june', 'july',
        '1st', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th', '10th', '11th', '12th', '13th', '14th', '15th', '16th', '17th', '18th', '19th', '20th', '21st', '22nd', '23rd', '24th', '25th', '26th', '27th', '28th', '29th', '30th', '31st',
        '2024', '2025', 'yesterday', 'today', 'last week', 'this week', 'last month', 'this month',
        '24 hours', 'last day', 'recent', 'last', 'from yesterday', 'past hour', 'past day', 'past week'
    ]):
        return [
            "kubectl get deployments --all-namespaces --sort-by=.metadata.creationTimestamp",
            "kubectl get deployments --all-namespaces -o jsonpath='{range .items[*]}{.metadata.name}{\"\\t\"}{.metadata.namespace}{\"\\t\"}{.metadata.creationTimestamp}{\"\\n\"}{end}'",
            "kubectl get events --all-namespaces --sort-by='.firstTimestamp' | grep -i deploy | tail -20"
        ]
    
    # Handle event queries
    elif any(term in prompt_lower for term in ['events', 'event', 'cluster events']):
        if any(time_term in prompt_lower for time_term in ['last', 'recent', 'today']):
            return ["kubectl get events --all-namespaces --sort-by='.firstTimestamp' | tail -50"]
        else:
            return ["kubectl get events --all-namespaces --sort-by='.firstTimestamp'"]
    
    elif any(term in prompt_lower for term in ['deployment', 'deployments']):
        if 'recent' in prompt_lower:
            return ["kubectl get deployments --all-namespaces --sort-by=.metadata.creationTimestamp"]
        elif 'how many' in prompt_lower:
            return ["kubectl get deployments --all-namespaces --no-headers | wc -l"]
        else:
            return ["kubectl get deployments --all-namespaces -o wide"]
    
    elif any(term in prompt_lower for term in ['node', 'nodes']):
        if 'taint' in prompt_lower:
            return ["kubectl get nodes -o custom-columns=NAME:.metadata.name,TAINTS:.spec.taints"]
        elif 'label' in prompt_lower:
            return ["kubectl get nodes --show-labels"]
        elif 'how many' in prompt_lower:
            return ["kubectl get nodes --no-headers | wc -l"]
        else:
            return ["kubectl get nodes -o wide"]
    
    elif any(term in prompt_lower for term in ['namespace', 'namespaces']):
        if 'how many' in prompt_lower:
            return ["kubectl get namespaces --no-headers | wc -l"]
        else:
            return ["kubectl get namespaces"]
    
    elif any(term in prompt_lower for term in ['storage', 'storageclass', 'sc']):
        return ["kubectl get storageclass"]
    
    elif any(term in prompt_lower for term in ['persistent volume', 'pv']):
        return ["kubectl get pv"]
    
    elif any(term in prompt_lower for term in ['pvc']):
        return ["kubectl get pvc --all-namespaces"]
    
    elif any(term in prompt_lower for term in ['ingress']):
        return ["kubectl get ingress --all-namespaces"]
    
    elif 'rbac' in prompt_lower:
        return [
            "kubectl get clusterroles",
            "kubectl get clusterrolebindings"
        ]
    
    return []