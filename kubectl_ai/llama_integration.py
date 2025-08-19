# llama_integration.py - Llama command generation and processing
import json
import re
from ollama import chat
from .safety import is_safe_command
from .query_detection import detect_query_type, detect_troubleshooting_intent, generate_cluster_info_commands
from .workflows import TROUBLESHOOTING_WORKFLOWS
# from llama_cpp import Llama

def build_system_prompt(query_type: str, entities: dict) -> str:
    """Build context-aware system prompts for different query types"""
    
    base_prompt = """You are a Kubernetes expert assistant that converts user queries into kubectl commands.

CRITICAL RULES:
1. ONLY generate read-only kubectl commands (get, describe, logs, top, explain, version, cluster-info)
2. NEVER generate destructive commands (delete, apply, create, edit, patch, replace, scale)
3. Use ONLY valid kubectl flags and options - no made-up flags like --recent
4. Return your response in this exact JSON format:
{
    "reasoning": "Brief explanation of your approach",
    "commands": ["kubectl command 1", "kubectl command 2", ...],
    "strategy": "troubleshooting|monitoring|assessment"
}

VALID kubectl get options:
- kubectl get pods/deployments/services [--all-namespaces] [-o wide/yaml/json] [--show-labels] [--sort-by=.metadata.creationTimestamp]
- kubectl get events [--sort-by='.firstTimestamp'] [--field-selector=...]
- kubectl top pods/nodes [--sort-by=cpu/memory]
- kubectl describe <resource> <name>
- kubectl logs <pod> [-n namespace] [--tail=N] [--previous]

For recent resources, use: --sort-by=.metadata.creationTimestamp
For time-based filtering, use kubectl get events with --sort-by='.firstTimestamp'

Available entities: """ + json.dumps(entities)

    if query_type == "troubleshooting":
        return base_prompt + """

TROUBLESHOOTING FOCUS:
- Generate a logical sequence of diagnostic commands
- Start with overview commands, then drill down to specifics
- Include logs, events, and describe commands for problematic resources
- Focus on the specific issue mentioned in the query

Example troubleshooting sequence:
1. kubectl get pods -n <namespace> -o wide (overview)
2. kubectl describe pod <pod-name> -n <namespace> (details)
3. kubectl logs <pod-name> -n <namespace> --tail=50 (recent logs)
4. kubectl get events -n <namespace> --sort-by='.firstTimestamp' (cluster events)
"""

    elif query_type == "assessment":
        return base_prompt + """

CLUSTER ASSESSMENT FOCUS:
- Generate commands that provide cluster-wide health overview
- Include node status, pod status across namespaces, and recent events
- Focus on identifying problems and resource usage
- Provide comprehensive cluster visibility

Example assessment sequence:
1. kubectl get nodes -o wide
2. kubectl get pods --all-namespaces | grep -v Running
3. kubectl top nodes
4. kubectl get events --all-namespaces --sort-by='.firstTimestamp' | tail -20
"""

    elif query_type == "resource":
        return base_prompt + """

RESOURCE ANALYSIS FOCUS:
- Generate commands to analyze resource usage and capacity
- Include both current usage (top) and configured limits
- Focus on identifying resource bottlenecks and usage patterns

Example resource sequence:
1. kubectl top pods --all-namespaces
2. kubectl top nodes
3. kubectl get pods -o jsonpath for resource specifications
"""

    elif query_type == "cluster_info":
        return base_prompt + """

CLUSTER INFO FOCUS:
- Generate commands to provide specific cluster information
- Focus on the exact information requested (nodes, namespaces, etc.)
- Keep it simple and direct
"""

    else:
        return base_prompt + """

GENERAL FOCUS:
- Analyze the user query to understand what they want to know
- Generate appropriate kubectl commands to answer their question
- If unclear, start with general overview commands
- For "recent" queries, use --sort-by=.metadata.creationTimestamp
- For deployment queries, use: kubectl get deployments --all-namespaces --sort-by=.metadata.creationTimestamp
- For events, use: kubectl get events --sort-by='.firstTimestamp'
- For time-based queries (last 24 hours, today, etc.), consider adding multiple commands:
  1. kubectl get deployments --all-namespaces --sort-by=.metadata.creationTimestamp
  2. kubectl get events --all-namespaces --sort-by='.firstTimestamp' | head -20 (for recent activity)
"""

def parse_llama_response(ai_response: str, context: dict) -> dict:
    """Parse Llama's response and extract commands and reasoning"""
    
    try:
        # Try to parse as JSON first
        if ai_response.strip().startswith('{'):
            # Clean up common JSON issues
            cleaned_response = ai_response.strip()
            # Remove trailing commas before closing braces/brackets
            cleaned_response = re.sub(r',(\s*[}\]])', r'\1', cleaned_response)
            
            parsed = json.loads(cleaned_response)
            commands = parsed.get("commands", [])
            reasoning = parsed.get("reasoning", "AI-generated kubectl commands")
            strategy = parsed.get("strategy", context["query_type"])
        else:
            # Fallback: extract kubectl commands from text
            commands = extract_kubectl_commands_from_text(ai_response)
            reasoning = "Extracted kubectl commands from AI response"
            strategy = context["query_type"]
        
        # Clean up commands - remove any malformed ones
        clean_commands = []
        for cmd in commands:
            if isinstance(cmd, str) and cmd.strip().startswith('kubectl '):
                # Remove any trailing quotes, commas, brackets
                clean_cmd = cmd.strip().rstrip('",]}').strip()
                # Basic validation - should have at least kubectl + action
                parts = clean_cmd.split()
                if len(parts) >= 2 and parts[0] == 'kubectl':
                    clean_commands.append(clean_cmd)
        
        # Validate and filter commands for safety
        safe_commands = []
        for cmd in clean_commands:
            if is_safe_command(cmd):
                safe_commands.append(cmd)
            else:
                print(f"Blocked unsafe command: {cmd}")
        
        return {
            "commands": safe_commands,
            "reasoning": reasoning,
            "strategy": strategy,
            "raw_response": ai_response
        }
        
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        # Fallback to text parsing
        commands = extract_kubectl_commands_from_text(ai_response)
        safe_commands = [cmd for cmd in commands if is_safe_command(cmd)]
        
        return {
            "commands": safe_commands,
            "reasoning": "Extracted commands from AI text response (JSON parsing failed)",
            "strategy": context["query_type"],
            "raw_response": ai_response
        }

def extract_kubectl_commands_from_text(text: str) -> list:
    """Extract kubectl commands from text response"""
    commands = []
    
    # Look for lines that start with kubectl
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith('kubectl '):
            # Clean up common formatting issues
            cmd = line.replace('```', '').replace('`', '').strip()
            # Remove trailing commas, quotes, and brackets
            cmd = cmd.rstrip('",]}')
            commands.append(cmd)
        elif 'kubectl ' in line:
            # Extract kubectl command from middle of line
            match = re.search(r'kubectl [^`\n"\']*', line)
            if match:
                cmd = match.group().strip()
                # Clean up trailing punctuation
                cmd = cmd.rstrip('",]}')
                commands.append(cmd)
    
    # Additional cleanup for common issues
    cleaned_commands = []
    for cmd in commands:
        # Remove any trailing quotes or punctuation
        cmd = cmd.strip().rstrip('",]}').strip()
        # Make sure it's a valid kubectl command
        if cmd.startswith('kubectl ') and len(cmd.split()) >= 2:
            cleaned_commands.append(cmd)
    
    return cleaned_commands

def enhance_commands_with_entities(commands: list, entities: dict) -> list:
    """Substitute entity placeholders in commands with actual values"""
    enhanced_commands = []
    
    for cmd in commands:
        enhanced_cmd = cmd
        
        # Replace common placeholders
        if "{pod_name}" in enhanced_cmd and "pod_name" in entities:
            enhanced_cmd = enhanced_cmd.replace("{pod_name}", entities["pod_name"])
        
        if "{namespace}" in enhanced_cmd and "namespace" in entities:
            enhanced_cmd = enhanced_cmd.replace("{namespace}", entities["namespace"])
        elif "{namespace}" in enhanced_cmd:
            # Default namespace if not specified
            enhanced_cmd = enhanced_cmd.replace("{namespace}", "default")
        
        # Replace generic placeholders with entity values
        if "<pod-name>" in enhanced_cmd and "pod_name" in entities:
            enhanced_cmd = enhanced_cmd.replace("<pod-name>", entities["pod_name"])
        
        if "<namespace>" in enhanced_cmd and "namespace" in entities:
            enhanced_cmd = enhanced_cmd.replace("<namespace>", entities["namespace"])
        elif "<namespace>" in enhanced_cmd:
            enhanced_cmd = enhanced_cmd.replace("<namespace>", "default")
        
        enhanced_commands.append(enhanced_cmd)
    
    return enhanced_commands

def generate_kubectl_commands_with_llama(prompt: str, entities: dict, query_type: str) -> dict:
    """Use Llama to generate kubectl commands from natural language"""
    
    # Build context for Llama
    context = {
        "query_type": query_type,
        "entities": entities,
        "user_prompt": prompt
    }
    
    # Create a targeted system prompt based on query type
    system_prompt = build_system_prompt(query_type, entities)
    
    try:
        response = chat(
            model="llama3",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        ai_response = response['message']['content'].strip()

        # llm = Llama.from_pretrained(
        #     repo_id="QuantFactory/Meta-Llama-3-8B-Instruct-GGUF",
        #     filename="Meta-Llama-3-8B-Instruct.Q2_K.gguf",
        # )
        # response = llm.create_chat_completion(
        #     messages=[
        #         {"role": "system", "content": system_prompt},
        #         {"role": "user", "content": prompt}
        #     ]
        # )
        # ai_response = response['choices'][0]['message']['content'].strip()
        
        # Extract commands and reasoning from Llama's response
        result = parse_llama_response(ai_response, context)
        
        return result
        
    except Exception as e:
        print(f"Llama generation failed: {e}")
        return {
            "commands": [],
            "reasoning": f"Failed to generate commands: {str(e)}",
            "strategy": "error"
        }

def generate_smart_commands_with_llama(prompt: str, entities: dict) -> list:
    """Main function to generate commands using Llama with intelligent context"""
    
    # Detect query type (keep your existing logic)
    query_type = detect_query_type(prompt)
    
    print(f"DEBUG: Using Llama for query type: {query_type}")
    print(f"DEBUG: Entities: {entities}")
    
    # For simple cluster info queries, use direct commands (faster)
    if query_type == 'cluster_info':
        return generate_cluster_info_commands(prompt)
    
    # For resource queries, use direct commands (more reliable)
    if query_type == 'resource':
        return generate_resource_commands(prompt)
    
    # Generate commands using Llama
    llama_result = generate_kubectl_commands_with_llama(prompt, entities, query_type)
    
    if not llama_result["commands"]:
        print("DEBUG: Llama failed to generate commands, using fallback")
        # Fallback to predefined workflows
        intent = detect_troubleshooting_intent(prompt)
        if intent and intent in TROUBLESHOOTING_WORKFLOWS:
            try:
                commands = []
                for cmd_template in TROUBLESHOOTING_WORKFLOWS[intent]:
                    cmd = cmd_template.format(**entities)
                    commands.append(cmd)
                return commands
            except KeyError:
                return []
        return []
    
    # Enhance commands with extracted entities
    enhanced_commands = enhance_commands_with_entities(llama_result["commands"], entities)
    
    print(f"DEBUG: Generated {len(enhanced_commands)} commands")
    print(f"DEBUG: Strategy: {llama_result['strategy']}")
    print(f"DEBUG: Reasoning: {llama_result['reasoning']}")
    
    return enhanced_commands

def generate_resource_commands(prompt: str) -> list:
    """Generate commands for resource analysis queries"""
    prompt_lower = prompt.lower()
    
    # Memory usage queries
    if any(pattern in prompt_lower for pattern in [
        'which pods use most memory', 'what pods use most memory', 'pods that use most memory',
        'highest memory', 'most memory', 'top memory', 'pod uses highest memory', 'pod using most memory'
    ]):
        return [
            "kubectl top pods --all-namespaces --sort-by=memory",
            "kubectl get pods --all-namespaces -o jsonpath='{range .items[*]}{.metadata.name}{\"\\t\"}{.metadata.namespace}{\"\\t\"}{.spec.containers[*].resources.requests.memory}{\"\\t\"}{.spec.containers[*].resources.limits.memory}{\"\\n\"}{end}'"
        ]
    
    # CPU usage queries
    elif any(pattern in prompt_lower for pattern in [
        'which pods use most cpu', 'what pods use most cpu', 'pods that use most cpu',
        'highest cpu', 'most cpu', 'top cpu', 'pod uses highest cpu', 'pod using most cpu'
    ]):
        return [
            "kubectl top pods --all-namespaces --sort-by=cpu",
            "kubectl get pods --all-namespaces -o jsonpath='{range .items[*]}{.metadata.name}{\"\\t\"}{.metadata.namespace}{\"\\t\"}{.spec.containers[*].resources.requests.cpu}{\"\\t\"}{.spec.containers[*].resources.limits.cpu}{\"\\n\"}{end}'"
        ]
    
    # General resource usage
    elif any(pattern in prompt_lower for pattern in [
        'resource usage', 'memory usage', 'cpu usage', 'performance', 'top pods'
    ]):
        return [
            "kubectl top pods --all-namespaces",
            "kubectl top nodes"
        ]
    
    # Node performance queries
    elif any(pattern in prompt_lower for pattern in [
        'node performance', 'show me node', 'node resource', 'node usage'
    ]):
        return [
            "kubectl top nodes",
            "kubectl get nodes -o wide",
            "kubectl describe nodes"
        ]
    
    # Default resource commands
    else:
        return [
            "kubectl top pods --all-namespaces",
            "kubectl top nodes"
        ]