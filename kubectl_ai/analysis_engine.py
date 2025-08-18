# analysis_engine.py - Analysis and pattern detection functions
import re

def analyze_failing_pods(command_outputs: dict) -> dict:
    """Analyze failing pods and provide focused answers"""
    analysis = {
        "answer": "",
        "details": [],
        "failing_pods": [],
        "recommendations": []
    }
    
    # Parse failing pods from field-selector output
    for cmd, output in command_outputs.items():
        if 'field-selector=status.phase!=Running' in cmd and output.strip():
            lines = output.strip().split('\n')[1:]  # Skip header
            if lines:
                analysis["failing_pods"] = []
                for line in lines:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 4:
                            namespace, pod_name, ready, status = parts[0], parts[1], parts[2], parts[3]
                            analysis["failing_pods"].append({
                                "name": pod_name,
                                "namespace": namespace,
                                "status": status,
                                "ready": ready
                            })
            break
    
    # If no failing pods from field-selector, try grep approach
    if not analysis["failing_pods"]:
        for cmd, output in command_outputs.items():
            if 'grep -E' in cmd and output.strip():
                lines = output.strip().split('\n')
                analysis["failing_pods"] = []
                for line in lines:
                    if line.strip() and any(status in line for status in ['Error', 'Failed', 'CrashLoopBackOff', 'ImagePullBackOff', 'Pending']):
                        parts = line.split()
                        if len(parts) >= 4:
                            namespace, pod_name, ready, status = parts[0], parts[1], parts[2], parts[3]
                            analysis["failing_pods"].append({
                                "name": pod_name,
                                "namespace": namespace,
                                "status": status,
                                "ready": ready
                            })
                break
    
    # Generate response based on findings
    if analysis["failing_pods"]:
        analysis["answer"] = f"🚨 **Found {len(analysis['failing_pods'])} failing pods in the cluster:**"
        
        # Group by status for better organization
        status_groups = {}
        for pod in analysis["failing_pods"]:
            status = pod["status"]
            if status not in status_groups:
                status_groups[status] = []
            status_groups[status].append(pod)
        
        for status, pods in status_groups.items():
            analysis["details"].append(f"\n**{status} ({len(pods)} pods):**")
            for pod in pods[:5]:  # Limit to 5 per status
                analysis["details"].append(f"  • **{pod['name']}** ({pod['namespace']} namespace) - Ready: {pod['ready']}")
        
        # Add specific recommendations based on status types
        if any(pod["status"] == "CrashLoopBackOff" for pod in analysis["failing_pods"]):
            analysis["recommendations"].append("🔍 For CrashLoopBackOff pods, check logs: `kubectl logs <pod-name> -n <namespace> --previous`")
        
        if any(pod["status"] == "ImagePullBackOff" for pod in analysis["failing_pods"]):
            analysis["recommendations"].append("🖼️ For ImagePullBackOff pods, verify image name and registry access")
        
        if any(pod["status"] == "Pending" for pod in analysis["failing_pods"]):
            analysis["recommendations"].append("⏳ For Pending pods, check resource availability: `kubectl describe pod <pod-name> -n <namespace>`")
        
        analysis["recommendations"].append("📋 Get detailed info: `kubectl describe pod <pod-name> -n <namespace>`")
        analysis["recommendations"].append("📊 Check recent events: `kubectl get events -n <namespace> --sort-by='.firstTimestamp'`")
        
    else:
        analysis["answer"] = "✅ **No failing pods found in the cluster!**"
        analysis["details"].append("All pods appear to be running normally across all namespaces.")
        analysis["recommendations"].append("🎉 Your cluster looks healthy! All pods are in Running state.")
    
    return analysis

def detect_issue_patterns(command_outputs: dict) -> dict:
    """K8sGPT-style intelligent pattern detection"""
    patterns = {
        "critical": [],
        "warnings": [],
        "info": []
    }
    
    # Pattern 1: Resource Pressure Detection
    for cmd, output in command_outputs.items():
        if 'kubectl top nodes' in cmd and output.strip() and 'NAME' in output:
            lines = output.strip().split('\n')[1:]
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 5:
                        node_name, cpu_usage, cpu_percent, memory_usage, memory_percent = parts[0:5]
                        
                        try:
                            cpu_pct = int(cpu_percent.replace('%', ''))
                            mem_pct = int(memory_percent.replace('%', ''))
                            
                            # Critical: Node exhaustion
                            if cpu_pct > 90 and mem_pct > 90:
                                patterns["critical"].append({
                                    "type": "NodeResourceExhaustion",
                                    "node": node_name,
                                    "details": f"CPU: {cpu_percent}, Memory: {memory_percent}",
                                    "explanation": "Node under severe resource pressure - pods may be evicted",
                                    "actions": ["Scale down workloads", "Add nodes", "Review resource limits"]
                                })
                            # Warning: High usage
                            elif cpu_pct > 80 or mem_pct > 80:
                                patterns["warnings"].append({
                                    "type": "NodeResourcePressure", 
                                    "node": node_name,
                                    "details": f"CPU: {cpu_percent}, Memory: {memory_percent}",
                                    "explanation": "Node approaching resource limits",
                                    "actions": ["Monitor closely", "Consider scaling"]
                                })
                        except:
                            pass
    
    # Pattern 2: High Restart Count Detection
    for cmd, output in command_outputs.items():
        if 'kubectl get pods --all-namespaces' in cmd and output.strip():
            lines = output.strip().split('\n')[1:]
            
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 5:
                        namespace, pod_name, ready, status, restarts = parts[0:5]
                        
                        # Pattern: High restart count
                        try:
                            restart_num = int(restarts.split('(')[0])
                            if restart_num > 10:
                                patterns["critical"].append({
                                    "type": "HighRestartCount",
                                    "resource": f"{namespace}/{pod_name}",
                                    "details": f"Restarted {restart_num} times",
                                    "explanation": "Pod repeatedly failing - indicates unstable application",
                                    "actions": [
                                        f"kubectl logs {pod_name} -n {namespace} --previous",
                                        "Check resource limits and health probes"
                                    ]
                                })
                            elif restart_num > 3:
                                patterns["warnings"].append({
                                    "type": "ModerateRestarts",
                                    "resource": f"{namespace}/{pod_name}",
                                    "details": f"Restarted {restart_num} times",
                                    "explanation": "Pod has restarted multiple times",
                                    "actions": ["Monitor logs for patterns"]
                                })
                        except:
                            pass
                        
                        # Pattern: Scheduling issues
                        if status == "Pending":
                            patterns["warnings"].append({
                                "type": "PodSchedulingIssue",
                                "resource": f"{namespace}/{pod_name}",
                                "details": "Pod stuck in Pending state",
                                "explanation": "Pod cannot be scheduled - likely resource constraints",
                                "actions": [
                                    f"kubectl describe pod {pod_name} -n {namespace}",
                                    "Check node capacity and taints"
                                ]
                            })
    
    return patterns

def analyze_cluster_health(command_outputs: dict) -> dict:
    """Analyze cluster-wide health and provide recommendations"""
    health_report = {
        "critical_issues": [],
        "warnings": [],
        "recommendations": [],
        "summary": {"total_pods": 0, "healthy_pods": 0, "problem_pods": 0, "nodes": 0}
    }
    
    # Analyze node health
    nodes_output = None
    for cmd in command_outputs:
        if "kubectl get nodes" in cmd:
            nodes_output = command_outputs[cmd]
            break
    
    if nodes_output:
        node_lines = nodes_output.strip().split('\n')[1:]  # Skip header
        for line in node_lines:
            if line.strip():
                parts = line.split()
                if len(parts) >= 2:
                    node_name, status = parts[0], parts[1]
                    health_report["summary"]["nodes"] += 1
                    if status != "Ready":
                        health_report["critical_issues"].append(f"Node {node_name} is in {status} state")
    
    # Analyze pod health across namespaces
    pods_output = None
    for cmd in command_outputs:
        if "kubectl get pods --all-namespaces" in cmd and "-o wide" in cmd:
            pods_output = command_outputs[cmd]
            break
    
    if pods_output:
        pod_lines = pods_output.strip().split('\n')[1:]  # Skip header
        
        namespace_stats = {}
        
        for line in pod_lines:
            if line.strip():
                parts = line.split()
                if len(parts) >= 4:
                    namespace, pod_name, ready, status = parts[0], parts[1], parts[2], parts[3]
                    health_report["summary"]["total_pods"] += 1
                    
                    # Track namespace stats
                    if namespace not in namespace_stats:
                        namespace_stats[namespace] = {"total": 0, "healthy": 0, "problems": 0}
                    namespace_stats[namespace]["total"] += 1
                    
                    if status == "Running" and "/" in ready:
                        ready_count, total_count = ready.split("/")
                        if ready_count == total_count:
                            health_report["summary"]["healthy_pods"] += 1
                            namespace_stats[namespace]["healthy"] += 1
                        else:
                            health_report["summary"]["problem_pods"] += 1
                            namespace_stats[namespace]["problems"] += 1
                            health_report["warnings"].append(f"Pod {pod_name} in {namespace} is not fully ready ({ready})")
                    elif status != "Running":
                        health_report["summary"]["problem_pods"] += 1
                        namespace_stats[namespace]["problems"] += 1
                        if status in ["CrashLoopBackOff", "Error", "Failed"]:
                            health_report["critical_issues"].append(f"Pod {pod_name} in {namespace} is in {status} state")
                        else:
                            health_report["warnings"].append(f"Pod {pod_name} in {namespace} is in {status} state")
        
        # Namespace-level recommendations
        for ns, stats in namespace_stats.items():
            if stats["problems"] > 0:
                health_report["recommendations"].append(f"Investigate {stats['problems']} problematic pods in {ns} namespace")
    
    # Generate overall recommendations
    total_pods = health_report["summary"]["total_pods"]
    problem_pods = health_report["summary"]["problem_pods"]
    
    if problem_pods == 0:
        health_report["recommendations"].append("✅ Cluster appears healthy - all pods are running normally")
    elif problem_pods / total_pods > 0.2:
        health_report["recommendations"].append(f"🔴 URGENT: {problem_pods}/{total_pods} pods have issues - investigate immediately")
    elif problem_pods > 0:
        health_report["recommendations"].append(f"🟡 Monitor: {problem_pods}/{total_pods} pods need attention")
    
    return health_report

def analyze_node_health(command_outputs: dict) -> dict:
    """Analyze node health and provide focused answers for node-specific queries"""
    analysis = {
        "answer": "",
        "details": [],
        "problematic_nodes": [],
        "recommendations": []
    }
    
    # Parse node status from kubectl get nodes
    for cmd, output in command_outputs.items():
        if 'kubectl get nodes -o wide' in cmd and output.strip():
            lines = output.strip().split('\n')[1:]  # Skip header
            if lines:
                total_nodes = 0
                ready_nodes = 0
                problematic_nodes = []
                
                for line in lines:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 2:
                            node_name, status = parts[0], parts[1]
                            total_nodes += 1
                            
                            if status == "Ready":
                                ready_nodes += 1
                            else:
                                problematic_nodes.append({
                                    "name": node_name,
                                    "status": status,
                                    "details": " ".join(parts[2:5]) if len(parts) > 4 else ""
                                })
                
                analysis["problematic_nodes"] = problematic_nodes
                
                if problematic_nodes:
                    analysis["answer"] = f"🚨 **Found {len(problematic_nodes)} problematic nodes out of {total_nodes} total:**"
                    
                    for node in problematic_nodes:
                        analysis["details"].append(f"• **{node['name']}**: Status = {node['status']}")
                        if node['details']:
                            analysis["details"].append(f"  Details: {node['details']}")
                else:
                    analysis["answer"] = f"✅ **All {total_nodes} nodes are healthy!**"
                    analysis["details"].append(f"All {total_nodes} nodes are in Ready state.")
                
                break
    
    # Check for resource pressure from kubectl top nodes
    resource_issues = []
    for cmd, output in command_outputs.items():
        if 'kubectl top nodes' in cmd and output.strip() and 'NAME' in output:
            lines = output.strip().split('\n')[1:]  # Skip header
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 5:
                        node_name, cpu_usage, cpu_percent, memory_usage, memory_percent = parts[0:5]
                        
                        try:
                            cpu_pct = int(cpu_percent.replace('%', ''))
                            mem_pct = int(memory_percent.replace('%', ''))
                            
                            if cpu_pct > 80 or mem_pct > 80:
                                resource_issues.append(f"**{node_name}**: High resource usage - CPU: {cpu_percent}, Memory: {memory_percent}")
                        except:
                            pass
    
    if resource_issues:
        analysis["details"].append("\n**Resource Pressure Detected:**")
        analysis["details"].extend(resource_issues)
    
    # Generate recommendations
    if analysis["problematic_nodes"]:
        analysis["recommendations"].extend([
            "🔍 Investigate node conditions: `kubectl describe node <node-name>`",
            "📊 Check node resource usage: `kubectl top nodes`",
            "📋 Review recent events: `kubectl get events --sort-by='.firstTimestamp'`",
            "🔧 Consider cordoning problematic nodes: `kubectl cordon <node-name>`"
        ])
    elif resource_issues:
        analysis["recommendations"].extend([
            "📈 Monitor resource trends over time",
            "🎯 Consider scaling down workloads or adding nodes",
            "🔍 Check which pods are consuming resources: `kubectl top pods --all-namespaces`"
        ])
    else:
        analysis["recommendations"].extend([
            "✅ Node health looks good!",
            "💡 Continue monitoring with: `kubectl top nodes`",
            "🔄 Regular health checks: `kubectl get nodes`"
        ])
    
    return analysis

def analyze_resource_usage(command_outputs: dict, prompt: str) -> dict:
    """Analyze resource usage and provide focused answers"""
    analysis = {
        "answer": "",
        "details": [],
        "recommendations": []
    }
    
    prompt_lower = prompt.lower()
    metrics_available = False
    
    # Check if we have metrics data
    for cmd, output in command_outputs.items():
        if 'kubectl top pods' in cmd and 'Metrics API not available' not in output and output.strip() and 'NAMESPACE' in output:
            metrics_available = True
            break
    
    if 'most memory' in prompt_lower or 'highest memory' in prompt_lower:
        if metrics_available:
            # Analyze actual usage from metrics
            for cmd, output in command_outputs.items():
                if 'kubectl top pods' in cmd and '--sort-by=memory' in cmd and output.strip():
                    lines = output.strip().split('\n')[1:]  # Skip header
                    if lines:
                        analysis["answer"] = "🔝 **Pods using most memory (actual usage):**"
                        for i, line in enumerate(lines[:5]):
                            if line.strip():
                                parts = line.split()
                                if len(parts) >= 4:
                                    namespace, pod_name, cpu, memory = parts[0], parts[1], parts[2], parts[3]
                                    analysis["details"].append(f"  {i+1}. **{pod_name}** ({namespace}): {memory}")
                        break
        
        if not metrics_available:
            analysis["recommendations"].extend([
                "💡 Install metrics-server to get real-time memory usage",
                "📊 Consider setting memory requests and limits for better resource management"
            ])
    
    elif 'node performance' in prompt_lower or 'show me node' in prompt_lower:
        analysis["answer"] = "🖥️ **Node Performance Overview:**"
        
        # Check for kubectl top nodes output
        for cmd, output in command_outputs.items():
            if 'kubectl top nodes' in cmd and output.strip() and 'NAME' in output:
                lines = output.strip().split('\n')[1:]  # Skip header
                if lines:
                    analysis["details"].append("**Current Resource Usage:**")
                    for line in lines:
                        if line.strip():
                            parts = line.split()
                            if len(parts) >= 5:
                                node_name, cpu_usage, cpu_percent, memory_usage, memory_percent = parts[0], parts[1], parts[2], parts[3], parts[4]
                                analysis["details"].append(f"  • **{node_name}**: CPU {cpu_usage} ({cpu_percent}) | Memory {memory_usage} ({memory_percent})")
                break
    
    return analysis

def analyze_command_output(cmd: str, output: str) -> dict:
    """Analyze kubectl command output to provide insights"""
    analysis = {"insights": [], "suggestions": []}
    
    if "kubectl get pod" in cmd and output:
        lines = output.strip().split('\n')[1:]  # Skip header
        for line in lines:
            parts = line.split()
            if len(parts) >= 3:
                status = parts[2]
                restarts = parts[3] if len(parts) > 3 else "0"
                
                if status == "CrashLoopBackOff":
                    analysis["insights"].append(f"Pod {parts[0]} is in CrashLoopBackOff state")
                    analysis["suggestions"].append("Container is exiting immediately - check command/args and logs")
                elif status != "Running":
                    analysis["insights"].append(f"Pod {parts[0]} is in {status} state")
                
                if restarts != "0":
                    try:
                        restart_count = int(restarts.split('(')[0])
                        if restart_count > 10:
                            analysis["insights"].append(f"Pod {parts[0]} has restarted {restart_count} times - indicating persistent failure")
                        else:
                            analysis["insights"].append(f"Pod {parts[0]} has restarted {restart_count} times")
                    except:
                        analysis["insights"].append(f"Pod {parts[0]} has restarted {restarts} times")
    
    elif "kubectl describe pod" in cmd:
        lines = output.split('\n')
        
        # Check for common issues
        if "Insufficient cpu" in output or "Insufficient memory" in output:
            analysis["insights"].append("Pod cannot be scheduled due to insufficient resources")
            analysis["suggestions"].append("Consider adjusting resource requests or adding more nodes")
        
        if "ImagePullBackOff" in output or "ErrImagePull" in output:
            analysis["insights"].append("Pod cannot pull the container image")
            analysis["suggestions"].append("Verify image name and registry accessibility")
        
        if "CrashLoopBackOff" in output:
            analysis["insights"].append("Pod is in crash loop - container exits immediately after starting")
            
            # Look for exit code
            if "Exit Code:" in output:
                exit_code_match = re.search(r'Exit Code:\s+(\d+)', output)
                if exit_code_match:
                    exit_code = exit_code_match.group(1)
                    if exit_code == "1":
                        analysis["suggestions"].append("Exit code 1 indicates general application error - check container command and application logic")
                    elif exit_code == "125":
                        analysis["suggestions"].append("Exit code 125 indicates Docker daemon error - check container configuration")
                    elif exit_code == "126":
                        analysis["suggestions"].append("Exit code 126 indicates command not executable - check file permissions and shebang")
                    elif exit_code == "127":
                        analysis["suggestions"].append("Exit code 127 indicates command not found - verify the command exists in container")
                    else:
                        analysis["suggestions"].append(f"Exit code {exit_code} - investigate application-specific error codes")
    
    elif "kubectl logs" in cmd:
        if not output.strip():
            analysis["insights"].append("No logs available - container may be exiting before producing output")
            analysis["suggestions"].append("Container exits too quickly to generate logs - check container entrypoint/command")
        else:
            error_indicators = ["error", "exception", "failed", "fatal", "panic", "traceback"]
            log_lines = output.lower().split('\n')
            
            error_found = False
            for line in log_lines:
                if any(indicator in line for indicator in error_indicators):
                    analysis["insights"].append("Found error messages in logs")
                    error_found = True
                    break
            
            if not error_found:
                analysis["insights"].append("No obvious error patterns in logs")
    
    return analysis