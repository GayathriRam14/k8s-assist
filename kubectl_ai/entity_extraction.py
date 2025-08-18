# entity_extraction.py - Entity detection and parsing

def requires_pod_context(text: str) -> bool:
    """Determine if the query actually needs pod/namespace extraction"""
    text_lower = text.lower()
    
    # Queries that definitely DON'T need pod context
    cluster_level_queries = [
        'how many nodes', 'list nodes', 'node', 'nodes',
        'taint', 'taints', 'labels on nodes', 'node labels',
        'cluster', 'namespaces', 'storage class', 'storageclass',
        'persistent volume', 'pv', 'pvc', 'ingress',
        'network policy', 'rbac', 'service account',
        'secrets', 'configmap', 'how many', 'count',
        'overview', 'status', 'health', 'assess'
    ]
    
    # If it's clearly a cluster-level query, don't extract pod entities
    if any(term in text_lower for term in cluster_level_queries):
        return False
    
    # Queries that DO need pod context
    pod_specific_indicators = [
        'pod', 'container', 'logs', 'debug pod', 'restart',
        'crashing', 'failing', 'not running', 'pending',
        'crash loop', 'image pull', 'describe pod'
    ]
    
    # Only extract pod entities if there are clear pod-related terms
    return any(indicator in text_lower for indicator in pod_specific_indicators)

def extract_entities(text: str) -> dict:
    """Extract various Kubernetes entities from user input - only when relevant"""
    entities = {}
    
    # First check if this query even needs pod/namespace extraction
    if not requires_pod_context(text):
        return entities  # Return empty dict for cluster-level queries
    
    words = text.lower().split()
    
    # Extract namespace - IMPROVED LOGIC
    namespace_value = None
    
    # Pattern 1: "in <namespace> namespace"
    for i, word in enumerate(words):
        if word == 'in' and i + 1 < len(words):
            next_word = words[i + 1]
            if i + 2 < len(words) and words[i + 2] == 'namespace':
                namespace_value = next_word
                break
        elif word in ['namespace', 'ns'] and i + 1 < len(words):
            namespace_value = words[i + 1]
            break
    
    # Pattern 2: "in <namespace>" (more flexible) - but be more selective
    if not namespace_value:
        for i, word in enumerate(words):
            if word == 'in' and i + 1 < len(words):
                potential_namespace = words[i + 1]
                # Clean punctuation first
                clean_namespace = potential_namespace.rstrip('?!.,;:')
                # Check if it's likely a namespace (not a common word)
                common_words = {'the', 'a', 'an', 'my', 'our', 'this', 'that', 'pod', 'container', 'cluster', 'debug', 'should', 'how', 'what', 'when', 'where', 'why'}
                if clean_namespace not in common_words and len(clean_namespace) > 2:
                    # Additional check: common namespace names
                    likely_namespaces = ['staging', 'production', 'prod', 'dev', 'development', 'test', 'testing', 'kube-system']
                    if clean_namespace in likely_namespaces:
                        namespace_value = clean_namespace
                        break
    
    # Pattern 3: Look for common namespace names only if context suggests it
    if not namespace_value and any(word in text.lower() for word in ['pod', 'container', 'deployment']):
        common_namespaces = ['staging', 'production', 'prod', 'dev', 'development', 'test', 'testing', 'kube-system']
        for word in words:
            if word in common_namespaces:
                namespace_value = word
                break
    
    if namespace_value:
        entities['namespace'] = namespace_value
    
    # Extract pod/deployment name - FIXED LOGIC
    pod_name = None
    exclude_words = {
        'is', 'the', 'and', 'or', 'in', 'on', 'at', 'to', 'for', 'with', 'by',
        'crashing', 'failing', 'running', 'starting', 'restarting', 'pending',
        'namespace', 'cluster', 'node', 'container', 'image', 'deployment',
        'service', 'why', 'what', 'how', 'when', 'where', 'check', 'debug',
        'staging', 'production', 'default', 'kube-system', 'resource', 'usage',
        'memory', 'cpu', 'pods', 'show', 'me', 'all', 'get', 'list', 'performance',
        'dev', 'prod', 'testing', 'should', 'i', 'my', 'a', 'an', 'start',
        'wont', "won't", 'not'
        # Removed 'test' since it can be a legitimate pod name
    }
    
    # Only look for pod names if there are clear pod-related terms
    if any(term in text.lower() for term in ['pod', 'container', 'debug', 'logs', 'describe']):
        
        # Strategy 1: Look for explicit "X pod" patterns
        for i, word in enumerate(words):
            if word == 'pod' and i > 0:
                potential_name = words[i-1]
                if potential_name not in exclude_words and len(potential_name) > 1:
                    pod_name = potential_name
                    break
        
        # Strategy 2: Look for deployment patterns
        if not pod_name:
            for i, word in enumerate(words):
                if word == 'deployment' and i > 0:
                    potential_name = words[i-1]
                    if potential_name not in exclude_words:
                        pod_name = f"{potential_name}-deployment"
                        break
                elif word.endswith('-deployment') and word not in exclude_words:
                    pod_name = word
                    break
        
        # Strategy 3: Look for pattern: "why won't X start" where X is the pod name
        if not pod_name:
            for i, word in enumerate(words):
                if word in ["won't", "wont"] and i + 1 < len(words) and words[i + 1] in ["start", "run"]:
                    # Look backwards for the subject
                    for j in range(i-1, -1, -1):
                        potential_name = words[j]
                        if potential_name not in exclude_words and len(potential_name) > 2:
                            pod_name = potential_name
                            break
                    if pod_name:
                        break
        
        # Strategy 4: Look for words that could be pod names (more restrictive)
        if not pod_name:
            for word in words:
                if (len(word) > 2 and 
                    word not in exclude_words and 
                    (word.isalnum() or '-' in word) and
                    # Additional check: does this look like a pod name?
                    (word.endswith('pod') or word.startswith('pod-') or 
                     '-' in word or word.endswith('-app') or word.endswith('-service') or
                     any(prefix in word for prefix in ['api-', 'web-', 'db-', 'cache-', 'worker-']))):
                    pod_name = word
                    break
    
    if pod_name:
        entities['pod_name'] = pod_name
    
    # Clean up extracted entities (remove punctuation)
    if 'namespace' in entities and entities['namespace']:
        entities['namespace'] = entities['namespace'].rstrip('?!.,;:')

    if 'pod_name' in entities and entities['pod_name']:
        entities['pod_name'] = entities['pod_name'].rstrip('?!.,;:')

    return entities