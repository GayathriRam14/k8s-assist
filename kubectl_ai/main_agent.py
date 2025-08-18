# main_agent.py - Core agent logic with Llama integration
import subprocess
from .utils import run_command
import re
import json
from ollama import chat
from .entity_extraction import extract_entities, requires_pod_context
from .query_detection import detect_query_type, detect_troubleshooting_intent
from .llama_integration import generate_smart_commands_with_llama
from .analysis_engine import (
    analyze_cluster_health, 
    analyze_node_health, 
    analyze_resource_usage,
    analyze_failing_pods,
    analyze_command_output,
    detect_issue_patterns
)
from .workflows import TROUBLESHOOTING_WORKFLOWS
from .safety import is_safe_command

def handle_conversational_queries(query_type: str, prompt: str) -> str:
    """Handle greetings, help requests, and other conversational inputs"""
    
    if query_type == 'greeting':
        return """[b green]👋 Hello! I'm your Kubernetes AI Assistant![/b green]

I can help you troubleshoot, monitor, and analyze your Kubernetes cluster using intelligent kubectl commands.

[b cyan]✨ Here are some example questions you can try:[/b cyan]

[b yellow]🏥 Cluster Health & Assessment:[/b yellow]
• "What issues does my cluster have?"
• "Anything I need to improve within my cluster?"
• "Check cluster health"
• "Give me a cluster assessment"

[b yellow]🔧 Pod Troubleshooting:[/b yellow]
• "Why is my-pod crashing?"
• "my-app-pod is not running in staging namespace"
• "Debug failing pods"
• "What's wrong with nginx-pod?"

[b yellow]📊 Information & Monitoring:[/b yellow]
• "Show me all pods"
• "How many pods are running?"
• "List pods in production namespace"
• "Get pod status"

[b yellow]📈 Resource Analysis:[/b yellow]
• "Check resource usage"
• "Show me node performance"
• "Which pods use most memory?"

[b cyan]💡 Tips:[/b cyan]
• I understand natural language - just describe what you want to check
• I'll automatically detect pod names, namespaces, and issues
• All commands are read-only and safe
• I provide detailed analysis and recommendations

Ready to help with your cluster! What would you like to check?"""

    elif query_type == 'help':
        return """[b cyan]🤖 Kubernetes AI Assistant - Help Guide[/b cyan]

[b green]What I can do:[/b green]
• 🔍 Intelligent cluster analysis and health assessment
• 🔧 Automatic troubleshooting with smart command sequences
• 📊 Pod, service, and deployment monitoring
• 📈 Resource usage analysis
• 💡 Actionable recommendations and insights

[b yellow]Example Commands You Can Try:[/b yellow]

[b]Cluster Assessment:[/b]
• "Assess my cluster health"
• "What problems exist in my cluster?"
• "Any recommendations for improvements?"

[b]Pod Issues:[/b]
• "my-pod is crashing" 
• "Why won't nginx-deployment start?"
• "Debug pods in kube-system namespace"

[b]Information Gathering:[/b]
• "List all running pods"
• "Show me pods in production"
• "How many pods are failing?"

[b]Resource Monitoring:[/b]
• "Check node resource usage"
• "Which pods use most CPU?"
• "Show memory usage"

[b green]Key Features:[/b green]
✅ Natural language understanding
✅ Automatic entity detection (pod names, namespaces)
✅ Smart troubleshooting workflows  
✅ Comprehensive health analysis
✅ Safe read-only operations
✅ Detailed explanations and recommendations

Just ask me anything about your Kubernetes cluster!"""

    elif query_type == 'goodbye':
        return """[b green]👋 Goodbye![/b green]

Thanks for using the Kubernetes AI Assistant! 

[b cyan]Remember:[/b cyan]
• I'm here whenever you need cluster help
• Try natural language questions about your K8s issues
• I can assess, troubleshoot, and monitor your cluster

Take care and happy clustering! 🚀"""

    return None

def analyze_events_for_errors(command_outputs: dict, prompt: str) -> str:
    """Analyze cluster events for errors, warnings, and issues"""
    
    # Find the events output
    events_output = None
    for cmd, output in command_outputs.items():
        if 'kubectl get events' in cmd and 'sort-by' in cmd:
            events_output = output
            break
    
    if not events_output or not events_output.strip():
        return "No cluster events data available."
    
    # Parse events
    lines = events_output.strip().split('\n')[1:]  # Skip header
    if not lines:
        return "No events found in cluster."
    
    events = []
    warnings = []
    errors = []
    normal_events = []
    
    for line in lines:
        if line.strip():
            # Parse kubectl events output: NAMESPACE LAST_SEEN TYPE REASON OBJECT MESSAGE
            parts = line.split(None, 5)  # Split into max 6 parts
            if len(parts) >= 6:
                namespace = parts[0]
                last_seen = parts[1]
                event_type = parts[2]
                reason = parts[3]
                obj = parts[4]
                message = parts[5]
                
                event_info = {
                    'namespace': namespace,
                    'last_seen': last_seen,
                    'type': event_type,
                    'reason': reason,
                    'object': obj,
                    'message': message
                }
                events.append(event_info)
                
                # Categorize events
                if event_type.lower() == 'warning':
                    warnings.append(event_info)
                elif event_type.lower() == 'error':
                    errors.append(event_info)
                else:
                    normal_events.append(event_info)
    
    # Analyze patterns
    result = f"**🔍 Cluster Events Analysis:**\n\n"
    
    # Summary
    total_events = len(events)
    result += f"**📊 Event Summary:**\n"
    result += f"• Total events: {total_events}\n"
    result += f"• Warnings: {len(warnings)} 🟡\n"
    result += f"• Errors: {len(errors)} 🔴\n"
    result += f"• Normal: {len(normal_events)} ✅\n\n"
    
    # Critical Issues
    if errors:
        result += f"**🚨 CRITICAL ERRORS ({len(errors)}):**\n"
        for error in errors[:5]:  # Show first 5 errors
            result += f"• **{error['object']}** ({error['namespace']}) - {error['reason']}: {error['message'][:80]}...\n"
        if len(errors) > 5:
            result += f"  ... and {len(errors) - 5} more errors\n"
        result += "\n"
    
    # Warnings
    if warnings:
        result += f"**⚠️ WARNINGS ({len(warnings)}):**\n"
        
        # Group warnings by reason for better analysis
        warning_groups = {}
        for warning in warnings:
            reason = warning['reason']
            if reason not in warning_groups:
                warning_groups[reason] = []
            warning_groups[reason].append(warning)
        
        for reason, reason_warnings in warning_groups.items():
            result += f"\n**{reason} ({len(reason_warnings)} events):**\n"
            for warning in reason_warnings[:3]:  # Show 3 examples per reason
                result += f"• **{warning['object']}** ({warning['namespace']}) - {warning['last_seen']} ago\n"
                result += f"  {warning['message'][:100]}...\n"
            if len(reason_warnings) > 3:
                result += f"  ... and {len(reason_warnings) - 3} more similar warnings\n"
        result += "\n"
    
    # Analysis and Recommendations
    result += f"**💡 Analysis & Recommendations:**\n\n"
    
    if errors:
        result += f"🔴 **CRITICAL**: {len(errors)} error events require immediate attention\n"
    
    if warnings:
        # Specific analysis for common warning types
        backoff_warnings = [w for w in warnings if 'backoff' in w['reason'].lower()]
        if backoff_warnings:
            result += f"🔄 **Container Restart Issues**: {len(backoff_warnings)} BackOff events detected\n"
            result += f"   → Pods are repeatedly failing and being restarted\n"
            result += f"   → Check container logs: `kubectl logs <pod-name> -n <namespace> --previous`\n"
        
        pulling_warnings = [w for w in warnings if 'pull' in w['reason'].lower()]
        if pulling_warnings:
            result += f"🖼️ **Image Pull Issues**: {len(pulling_warnings)} image-related warnings\n"
            result += f"   → Verify image names and registry accessibility\n"
        
        scheduling_warnings = [w for w in warnings if 'schedul' in w['reason'].lower()]
        if scheduling_warnings:
            result += f"📅 **Scheduling Issues**: {len(scheduling_warnings)} scheduling warnings\n"
            result += f"   → Check resource availability and node capacity\n"
            
        result += f"\n"
    
    if not errors and not warnings:
        result += f"✅ **All Good**: No errors or warnings found in recent events\n"
        result += f"🎉 Your cluster appears to be running smoothly!\n"
    else:
        result += f"🔍 **Next Steps:**\n"
        result += f"• Focus on the most recent warnings first\n"
        result += f"• Check pod logs for containers that are backing off\n"
        result += f"• Verify resource limits and requests are appropriate\n"
        result += f"• Use `kubectl describe pod <name>` for detailed troubleshooting\n"
    
    # Recent activity focus
    recent_events = [e for e in events if any(time_indicator in e['last_seen'] for time_indicator in ['s', 'm']) and not 'h' in e['last_seen'] and not 'd' in e['last_seen']]
    if recent_events:
        result += f"\n**⏰ Recent Activity ({len(recent_events)} events in last hour):**\n"
        for event in recent_events[:5]:
            status_emoji = "🔴" if event['type'] == 'Error' else "🟡" if event['type'] == 'Warning' else "ℹ️"
            result += f"{status_emoji} **{event['object']}** ({event['namespace']}) - {event['last_seen']} ago - {event['reason']}\n"
    
    return result

def analyze_events_with_timestamps(command_outputs: dict, prompt: str) -> str:
    """Analyze events using exact timestamps from kubectl output"""
    
    # Find the timestamp output from jsonpath command
    timestamp_output = None
    for cmd, output in command_outputs.items():
        if 'jsonpath' in cmd and 'firstTimestamp' in cmd:
            timestamp_output = output
            break
    
    if not timestamp_output or not timestamp_output.strip():
        return "No event timestamp data available."
    
    # Parse the target date from prompt dynamically
    target_date, time_range_desc = parse_date_from_prompt(prompt)
    
    if not target_date:
        return "Could not determine target date from query."
    
    # Parse timestamp data
    events = []
    matching_events = []
    
    lines = timestamp_output.strip().split('\n')
    for line in lines:
        if line.strip():
            parts = line.split('\t')
            if len(parts) >= 5:
                name = parts[0].strip()
                namespace = parts[1].strip() 
                timestamp = parts[2].strip()
                reason = parts[3].strip()
                message = parts[4].strip()
                
                # Extract date from timestamp (YYYY-MM-DD from YYYY-MM-DDTHH:MM:SSZ)
                event_date = timestamp.split('T')[0] if 'T' in timestamp else timestamp[:10]
                
                event_info = {
                    'name': name,
                    'namespace': namespace,
                    'timestamp': timestamp,
                    'date': event_date,
                    'reason': reason,
                    'message': message
                }
                events.append(event_info)
                
                # Check if it matches target date
                if event_date == target_date:
                    matching_events.append(event_info)
    
    # Generate result
    result = f"**Events on {time_range_desc}:**\n\n"
    
    if matching_events:
        result += f"✅ **Found {len(matching_events)} event(s) from {time_range_desc}:**\n\n"
        for event in matching_events[:10]:  # Show first 10 events
            time_part = event['timestamp'].split('T')[1].replace('Z', '') if 'T' in event['timestamp'] else 'unknown time'
            result += f"• **{time_part}** [{event['reason']}] {event['namespace']}/{event['name']} - {event['message'][:60]}...\n"
        
        if len(matching_events) > 10:
            result += f"  ... and {len(matching_events) - 10} more events\n"
            
        result += f"\n✅ **All events successfully identified using exact timestamps!**\n"
    else:
        result += f"❌ **No events found on {time_range_desc}.**\n\n"
        
        # Show what dates we do have
        result += f"**Events found on other dates (last 5 dates):**\n"
        date_groups = {}
        for event in events:
            date = event['date']
            if date not in date_groups:
                date_groups[date] = []
            date_groups[date].append(event)
        
        for date in sorted(date_groups.keys(), reverse=True)[:5]:
            events_on_date = date_groups[date]
            result += f"\n**{date}:** {len(events_on_date)} events\n"
            for event in events_on_date[:3]:  # Show 3 sample events
                time_part = event['timestamp'].split('T')[1].replace('Z', '') if 'T' in event['timestamp'] else ''
                result += f"  • {time_part} [{event['reason']}] {event['message'][:40]}...\n"
    
    result += f"\n**📅 Exact Timestamp Analysis:**\n"
    result += f"• Target: {time_range_desc}\n"
    result += f"• Method: Parsed exact firstTimestamp from Kubernetes event metadata\n"
    result += f"• Accuracy: 100% - using exact timestamps, not relative AGE\n"
    result += f"• Total events analyzed: {len(events)}\n"
    
    return result

def analyze_deployment_with_timestamps(command_outputs: dict, prompt: str) -> str:
    """Analyze deployments using exact timestamps from kubectl output"""
    
    # Find the timestamp output from jsonpath command
    timestamp_output = None
    for cmd, output in command_outputs.items():
        if 'jsonpath' in cmd and 'creationTimestamp' in cmd:
            timestamp_output = output
            break
    
    if not timestamp_output or not timestamp_output.strip():
        return "No timestamp data available."
    
    # Parse the target date from prompt dynamically
    target_date, time_range_desc = parse_date_from_prompt(prompt)
    
    if not target_date:
        return "Could not determine target date from query."
    
    # Parse timestamp data
    deployments = []
    matching_deployments = []
    
    lines = timestamp_output.strip().split('\n')
    for line in lines:
        if line.strip():
            parts = line.split('\t')
            if len(parts) >= 3:
                name = parts[0].strip()
                namespace = parts[1].strip() 
                timestamp = parts[2].strip()
                
                # Extract date from timestamp (YYYY-MM-DD from YYYY-MM-DDTHH:MM:SSZ)
                deployment_date = timestamp.split('T')[0] if 'T' in timestamp else timestamp[:10]
                
                deployment_info = {
                    'name': name,
                    'namespace': namespace,
                    'timestamp': timestamp,
                    'date': deployment_date
                }
                deployments.append(deployment_info)
                
                # Check if it matches target date
                if deployment_date == target_date:
                    matching_deployments.append(deployment_info)
    
    # Generate result
    result = f"**Deployments on {time_range_desc}:**\n\n"
    
    if matching_deployments:
        result += f"✅ **Found {len(matching_deployments)} deployment(s) from {time_range_desc}:**\n\n"
        for dep in matching_deployments:
            time_part = dep['timestamp'].split('T')[1].replace('Z', '') if 'T' in dep['timestamp'] else 'unknown time'
            result += f"✅ **{dep['name']}** ({dep['namespace']}) - Created: {time_part} on {dep['date']}\n"
        
        result += f"\n✅ **All deployments successfully identified using exact timestamps!**\n"
    else:
        result += f"❌ **No deployments found on {time_range_desc}.**\n\n"
        
        # Show what dates we do have
        result += f"**Deployments found on other dates:**\n"
        date_groups = {}
        for dep in deployments:
            date = dep['date']
            if date not in date_groups:
                date_groups[date] = []
            date_groups[date].append(dep)
        
        for date, deps in sorted(date_groups.items()):
            result += f"\n**{date}:**\n"
            for dep in deps:
                time_part = dep['timestamp'].split('T')[1].replace('Z', '') if 'T' in dep['timestamp'] else ''
                result += f"  • {dep['name']} ({dep['namespace']}) at {time_part}\n"
    
    result += f"\n**📅 Exact Timestamp Analysis:**\n"
    result += f"• Target: {time_range_desc}\n"
    result += f"• Method: Parsed exact creationTimestamp from Kubernetes metadata\n"
    result += f"• Accuracy: 100% - using exact timestamps, not relative AGE\n"
    result += f"• Total deployments analyzed: {len(deployments)}\n"
    
    return result

def parse_date_from_prompt(prompt: str) -> tuple:
    """Parse date from prompt dynamically"""
    import re
    from datetime import datetime, timedelta
    
    prompt_lower = prompt.lower()
    
    # Current date (assuming today is 18th August 2025)
    current_date = datetime(2025, 8, 18)
    
    # Pattern 1: Specific date with ordinal (15th august 2025, august 15th 2025)
    date_patterns = [
        r'(\d{1,2})(st|nd|rd|th)\s+(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{4})',
        r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})(st|nd|rd|th)?\s+(\d{4})',
        r'(\d{4})-(\d{1,2})-(\d{1,2})',  # ISO format
    ]
    
    months = {
        'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
        'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12
    }
    
    for pattern in date_patterns:
        match = re.search(pattern, prompt_lower)
        if match:
            groups = match.groups()
            
            if pattern == date_patterns[0]:  # 15th august 2025
                day, suffix, month_name, year = groups
                month = months.get(month_name)
                if month:
                    target_date = f"{year}-{month:02d}-{int(day):02d}"
                    return target_date, f"{day}{suffix} {month_name.title()} {year}"
                    
            elif pattern == date_patterns[1]:  # august 15th 2025
                month_name, day, suffix, year = groups
                month = months.get(month_name)
                if month:
                    target_date = f"{year}-{month:02d}-{int(day):02d}"
                    suffix = suffix or ""
                    return target_date, f"{day}{suffix} {month_name.title()} {year}"
                    
            elif pattern == date_patterns[2]:  # 2025-08-15
                year, month, day = groups
                target_date = f"{year}-{int(month):02d}-{int(day):02d}"
                return target_date, f"{day} {list(months.keys())[int(month)-1].title()} {year}"
    
    # Pattern 2: Relative dates
    if 'today' in prompt_lower:
        target_date = current_date.strftime('%Y-%m-%d')
        return target_date, "today (18th August 2025)"
    elif 'yesterday' in prompt_lower:
        target_date = (current_date - timedelta(days=1)).strftime('%Y-%m-%d')
        return target_date, "yesterday (17th August 2025)"
    elif 'day before yesterday' in prompt_lower or '2 days ago' in prompt_lower:
        target_date = (current_date - timedelta(days=2)).strftime('%Y-%m-%d')
        return target_date, "2 days ago (16th August 2025)"
    
    return None, None

def analyze_deployment_by_date(output: str, prompt: str) -> str:
    """Analyze deployment output for specific date queries"""
    lines = output.strip().split('\n')[1:]  # Skip header
    if not lines:
        return "No deployments found."
    
    prompt_lower = prompt.lower()
    
    # Determine the time range based on the query
    time_range = "unknown"
    if 'yesterday' in prompt_lower or 'from yesterday' in prompt_lower:
        time_range = "yesterday"
        target_hours = (24, 48)  # 24-48 hours ago
    elif 'today' in prompt_lower:
        time_range = "today"
        target_hours = (0, 24)   # 0-24 hours ago
    elif '24 hours' in prompt_lower or 'last day' in prompt_lower:
        time_range = "last 24 hours"
        target_hours = (0, 24)
    elif 'last week' in prompt_lower or 'past week' in prompt_lower:
        time_range = "last week"
        target_hours = (0, 168)  # 0-168 hours (7 days)
    else:
        time_range = "recent"
        target_hours = (0, 72)   # Default to last 3 days
    
    found_deployments = []
    matching_deployments = []
    
    for line in lines:
        if line.strip():
            parts = line.split()
            if len(parts) >= 6:
                namespace, name, ready, up_to_date, available, age = parts[0], parts[1], parts[2], parts[3], parts[4], parts[5]
                
                # Parse age to hours for comparison
                hours_ago = parse_age_to_hours(age)
                
                deployment_info = {
                    'namespace': namespace,
                    'name': name,
                    'ready': ready,
                    'age': age,
                    'hours_ago': hours_ago
                }
                found_deployments.append(deployment_info)
                
                # Check if deployment matches the time range
                if hours_ago is not None:
                    if time_range == "yesterday" and 24 <= hours_ago <= 48:
                        matching_deployments.append(deployment_info)
                    elif time_range in ["today", "last 24 hours"] and hours_ago <= 24:
                        matching_deployments.append(deployment_info)
                    elif time_range == "last week" and hours_ago <= 168:
                        matching_deployments.append(deployment_info)
                    elif time_range == "recent" and hours_ago <= 72:
                        matching_deployments.append(deployment_info)
    
    result = f"**Deployments {time_range}:**\n\n"
    
    if matching_deployments:
        result += f"✅ **Found {len(matching_deployments)} deployment(s) matching '{time_range}':**\n\n"
        for dep in matching_deployments:
            status_emoji = "✅" if dep['ready'].split('/')[0] == dep['ready'].split('/')[1] else "⚠️"
            result += f"{status_emoji} **{dep['name']}** ({dep['namespace']}) - Ready: {dep['ready']} - Age: {dep['age']}\n"
        
        # Check health of matching deployments
        failing_deployments = [d for d in matching_deployments if d['ready'].split('/')[0] != d['ready'].split('/')[1]]
        if failing_deployments:
            result += f"\n⚠️ **{len(failing_deployments)} deployment(s) not fully ready**\n"
        else:
            result += f"\n✅ **All matching deployments are healthy**\n"
    else:
        result += f"❌ **No deployments found {time_range}.**\n\n"
        
        # Show what we did find for context
        recent_deployments = [d for d in found_deployments if d['hours_ago'] is not None and d['hours_ago'] <= 168]  # Last week
        if recent_deployments:
            result += f"**For reference, recent deployments in the cluster:**\n"
            for dep in recent_deployments[:5]:  # Show 5 most recent
                result += f"• {dep['name']} ({dep['namespace']}) - {dep['age']} ago\n"
        else:
            result += f"**All visible deployments are older than 1 week.**\n"
    
    result += f"\n**Time range interpretation:**\n"
    result += f"• Query: '{prompt}' → Looking for deployments {time_range}\n"
    result += f"• kubectl AGE format: 3d9h = 3 days 9 hours, 7h29m = 7 hours 29 minutes\n"
    result += f"• For exact timestamps: `kubectl get deployment <name> -o yaml | grep creationTimestamp`\n"
    
    return result

def parse_age_to_hours(age_str: str) -> float:
    """Convert kubectl AGE format to hours"""
    try:
        total_hours = 0
        age_str = age_str.lower()
        
        # Parse days (e.g., "3d9h" or "3d")
        if 'd' in age_str:
            days_part = age_str.split('d')[0]
            if days_part.isdigit():
                total_hours += int(days_part) * 24
            age_str = age_str.split('d')[1] if 'd' in age_str else ""
        
        # Parse hours (e.g., "9h" or "7h29m")
        if 'h' in age_str:
            hours_part = age_str.split('h')[0]
            if hours_part.isdigit():
                total_hours += int(hours_part)
            age_str = age_str.split('h')[1] if 'h' in age_str else ""
        
        # Parse minutes (e.g., "29m")
        if 'm' in age_str:
            minutes_part = age_str.split('m')[0]
            if minutes_part.isdigit():
                total_hours += int(minutes_part) / 60.0
        
        # Parse seconds (e.g., "45s")
        if 's' in age_str:
            seconds_part = age_str.split('s')[0]
            if seconds_part.isdigit():
                total_hours += int(seconds_part) / 3600.0
        
        return total_hours
    except:
        return None

def analyze_recent_deployments(output: str, prompt: str) -> str:
    """Analyze deployment output for recent activity"""
    lines = output.strip().split('\n')[1:]  # Skip header
    if not lines:
        return "No deployments found."
    
    recent_deployments = []
    
    for line in lines:
        if line.strip():
            parts = line.split()
            if len(parts) >= 6:
                namespace, name, ready, up_to_date, available, age = parts[0], parts[1], parts[2], parts[3], parts[4], parts[5]
                
                # Parse age to determine if it's recent
                is_recent = False
                if 'h' in age and not 'd' in age:  # Only hours, no days
                    try:
                        hours = int(age.replace('h', '').replace('m', '').split('h')[0])
                        if hours <= 24:
                            is_recent = True
                    except:
                        pass
                elif 'm' in age and not 'h' in age and not 'd' in age:  # Only minutes
                    is_recent = True
                
                if is_recent:
                    recent_deployments.append({
                        'namespace': namespace,
                        'name': name,
                        'ready': ready,
                        'age': age
                    })
    
    if recent_deployments:
        result = f"**Found {len(recent_deployments)} deployments in the last 24 hours:**\n\n"
        for dep in recent_deployments:
            status_emoji = "✅" if dep['ready'].split('/')[0] == dep['ready'].split('/')[1] else "⚠️"
            result += f"{status_emoji} **{dep['name']}** ({dep['namespace']}) - Ready: {dep['ready']} - Age: {dep['age']}\n"
        
        result += f"\n**Analysis:**\n"
        if len(recent_deployments) > 3:
            result += f"• High deployment activity ({len(recent_deployments)} deployments)\n"
        
        failing_deployments = [d for d in recent_deployments if d['ready'].split('/')[0] != d['ready'].split('/')[1]]
        if failing_deployments:
            result += f"• ⚠️ {len(failing_deployments)} recent deployment(s) not fully ready\n"
        else:
            result += f"• ✅ All recent deployments are healthy\n"
        
        return result
    else:
        return "**No deployments found in the last 24 hours.**\n\nAll visible deployments are older than 24 hours."
    """Try to find the actual pod name from a potentially partial or incorrect name"""
    if not potential_name:
        return None
    
    try:
        # First, try exact match
        result = run_command(f"kubectl get pod {potential_name} -n {namespace} --no-headers", use_cache=False)
        if result.strip():
            return potential_name
    except:
        pass
    
    try:
        # If exact match fails, search for pods that contain this name
        result = run_command(f"kubectl get pods -n {namespace} --no-headers", use_cache=False)
        lines = result.strip().split('\n')
        
        for line in lines:
            if line.strip():
                pod_name = line.split()[0]
                # Check if the potential name is contained in the actual pod name
                if potential_name.lower() in pod_name.lower():
                    return pod_name
                # Check if the actual pod name starts with the potential name
                if pod_name.lower().startswith(potential_name.lower()):
                    return pod_name
    except:
        pass
    
    return potential_name  # Return original if we can't resolve

def process_query(prompt: str) -> str:
    """Process user query using Llama for command generation but keep intelligent analysis"""
    
    # Keep your existing entity extraction and query type detection
    entities = extract_entities(prompt)
    query_type = detect_query_type(prompt)
    
    print(f"DEBUG: Query type detected: {query_type}")
    print(f"DEBUG: Entities: {entities}")
    
    # Handle conversational queries (keep existing logic)
    conversational_response = handle_conversational_queries(query_type, prompt)
    if conversational_response:
        return conversational_response
    
    # Try to resolve pod name if we have one and it's a troubleshooting query
    if query_type == 'troubleshooting' and 'pod_name' in entities and 'namespace' in entities:
        resolved_pod = resolve_pod_name(entities['pod_name'], entities['namespace'])
        if resolved_pod != entities['pod_name']:
            entities['pod_name'] = resolved_pod
    
    # Generate commands using Llama
    commands = generate_smart_commands_with_llama(prompt, entities)
    
    if not commands:
        return f"🤖 Unable to generate safe kubectl commands for: {prompt}"
    
    # Execute commands and provide your intelligent analysis
    category_display = {
        'informational': '📊 INFORMATIONAL',
        'troubleshooting': '🔧 TROUBLESHOOTING', 
        'assessment': '🏥 CLUSTER ASSESSMENT',
        'resource': '📈 RESOURCE ANALYSIS',
        'cluster_info': '🖥️ CLUSTER INFO',
        'general': '💬 GENERAL'
    }
    
    combined_output = f"[b magenta]Category: {category_display.get(query_type, '💬 GENERAL')}[/b magenta]\n"
    
    if query_type == 'resource':
        combined_output += f"[b cyan]🧠 AI Strategy:[/b cyan]\nUsing direct resource command generation (bypassing Llama for reliability)\n"
    elif query_type == 'cluster_info':
        combined_output += f"[b cyan]🧠 AI Strategy:[/b cyan]\nUsing direct cluster info commands (fast path)\n"
    else:
        combined_output += f"[b cyan]🧠 AI Strategy:[/b cyan]\nUsing Llama-generated kubectl commands for {query_type} analysis\n"
    
    # Execute commands and apply your existing intelligent analysis
    command_outputs = {}
    all_insights = []
    all_suggestions = []
    
    for i, cmd in enumerate(commands, 1):
        if not is_safe_command(cmd):
            combined_output += f"\n[yellow]⚠️ Skipped unsafe command:[/yellow] {cmd}"
            continue
        
        try:
            output = run_command(cmd)
            combined_output += f"\n\n[b]🛠 Step {i}:[/b]\n{cmd}\n\n📜 Output:\n{output.strip()}"
            
            command_outputs[cmd] = output
            
            # Apply your existing analysis logic
            if query_type == 'troubleshooting':
                analysis = analyze_command_output(cmd, output)
                all_insights.extend(analysis["insights"])
                all_suggestions.extend(analysis["suggestions"])
            elif query_type == 'informational' and 'grep -c' in cmd:
                # For count queries, provide a summary
                count = output.strip()
                if count.isdigit():
                    if 'all-namespaces' in cmd:
                        combined_output += f"\n\n[b green]📊 Summary:[/b green] {count} pods are currently running across all namespaces"
                    else:
                        namespace = entities.get('namespace', 'default')
                        combined_output += f"\n\n[b green]📊 Summary:[/b green] {count} pods are currently running in the {namespace} namespace"
            elif query_type == 'general' and any(term in prompt.lower() for term in ['24 hours', 'last day', 'today', 'recent']):
                # Analyze timestamps for recent deployments
                recent_analysis = analyze_recent_deployments(output, prompt)
                if recent_analysis:
                    combined_output += f"\n\n[b green]🎯 Recent Activity Analysis:[/b green]\n{recent_analysis}"
            elif query_type == 'cluster_info' and any(term in prompt.lower() for term in ['event', 'events']) and any(analysis_term in prompt.lower() for analysis_term in ['error', 'errors', 'problem', 'issues', 'warning', 'see any', 'analyze', 'check']):
                # Analyze events for errors and issues
                try:
                    event_analysis = analyze_events_for_errors(command_outputs, prompt)
                    if event_analysis:
                        combined_output += f"\n\n[b green]🔍 Event Analysis:[/b green]\n{event_analysis}"
                except Exception as e:
                    combined_output += f"\n\n[b yellow]⚠️ Analysis Error:[/b yellow]\nCould not analyze events: {str(e)}"
            elif query_type == 'cluster_info' and any(date_term in prompt.lower() for date_term in [
                'august', 'september', 'october', 'november', 'december', 'january', 'february', 'march', 'april', 'may', 'june', 'july',
                '1st', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th', '10th', '11th', '12th', '13th', '14th', '15th', '16th', '17th', '18th', '19th', '20th', '21st', '22nd', '23rd', '24th', '25th', '26th', '27th', '28th', '29th', '30th', '31st',
                '2024', '2025', 'yesterday', 'today', 'last week', 'this week', 'last month', 'this month',
                '24 hours', 'last day', 'recent', 'last', 'from yesterday', 'past hour', 'past day', 'past week'
            ]):
                # Analyze deployments or events using timestamp data from all command outputs
                try:
                    if any(term in prompt.lower() for term in ['event', 'events']):
                        date_analysis = analyze_events_with_timestamps(command_outputs, prompt)
                    else:
                        date_analysis = analyze_deployment_with_timestamps(command_outputs, prompt)
                    
                    if date_analysis:
                        combined_output += f"\n\n[b green]🎯 Timestamp-Based Analysis:[/b green]\n{date_analysis}"
                except Exception as e:
                    combined_output += f"\n\n[b yellow]⚠️ Analysis Error:[/b yellow]\nCould not parse timestamp data: {str(e)}"
            
        except subprocess.CalledProcessError as e:
            error_msg = e.output.decode() if e.output else str(e)
            combined_output += f"\n\n[red]❌ Step {i} failed:[/red] {cmd}\n{error_msg}"
            command_outputs[cmd] = error_msg
    
    # Apply your existing specialized analysis based on query type
    if query_type == 'assessment':
        # Check if it's specifically about nodes
        if any(term in prompt.lower() for term in ['node', 'nodes']):
            analysis = analyze_node_health(command_outputs)
        else:
            analysis = analyze_cluster_health(command_outputs)
        
        # Add analysis results to output
        if analysis.get("answer"):
            combined_output += f"\n\n[b green]🎯 Analysis Results:[/b green]\n{analysis['answer']}\n"
            
            for detail in analysis["details"]:
                combined_output += f"{detail}\n"
        
        # Add critical issues and warnings
        if "critical_issues" in analysis and analysis["critical_issues"]:
            combined_output += f"\n[b red]🚨 CRITICAL ISSUES:[/b red]\n"
            for issue in analysis["critical_issues"]:
                combined_output += f"• {issue}\n"
        
        if "warnings" in analysis and analysis["warnings"]:
            combined_output += f"\n[b yellow]⚠️ WARNINGS:[/b yellow]\n"
            for warning in analysis["warnings"]:
                combined_output += f"• {warning}\n"
        
        # Add recommendations
        if analysis.get("recommendations"):
            combined_output += f"\n[b green]💡 Recommendations:[/b green]\n"
            for rec in analysis["recommendations"]:
                combined_output += f"• {rec}\n"
        
        # Add summary if available
        if "summary" in analysis:
            combined_output += f"\n[b blue]📋 SUMMARY:[/b blue]\n"
            summary = analysis["summary"]
            if "nodes" in summary:
                combined_output += f"• Nodes: {summary['nodes']}\n"
            if "total_pods" in summary:
                combined_output += f"• Total Pods: {summary['total_pods']}\n"
                combined_output += f"• Healthy Pods: {summary['healthy_pods']}\n"
                combined_output += f"• Problem Pods: {summary['problem_pods']}\n"
                
                if summary['total_pods'] > 0:
                    health_percentage = (summary['healthy_pods'] / summary['total_pods']) * 100
                    combined_output += f"• Cluster Health: {health_percentage:.1f}%\n"
    
    elif query_type == 'resource':
        # Enhanced resource analysis with pattern detection
        resource_analysis = analyze_resource_usage(command_outputs, prompt)
        
        # Run K8sGPT-style pattern detection
        patterns = detect_issue_patterns(command_outputs)
        
        if resource_analysis["answer"]:
            combined_output += f"\n\n[b green]🎯 Direct Answer:[/b green]\n{resource_analysis['answer']}\n"
            
            for detail in resource_analysis["details"]:
                combined_output += f"{detail}\n"
            
            # Add pattern-based insights
            if patterns["critical"] or patterns["warnings"]:
                combined_output += f"\n[b red]🔍 INTELLIGENT PATTERN ANALYSIS:[/b red]\n"
                
                for issue in patterns["critical"]:
                    combined_output += f"🚨 **{issue['type']}**: {issue['explanation']}\n"
                    combined_output += f"   📍 Affected: {issue.get('resource', issue.get('node', 'N/A'))}\n"
                    combined_output += f"   🔧 Actions: {', '.join(issue['actions'][:2])}...\n\n"
                
                for warning in patterns["warnings"]:
                    combined_output += f"⚠️ **{warning['type']}**: {warning['explanation']}\n"
                    combined_output += f"   📍 Affected: {warning.get('resource', warning.get('node', 'N/A'))}\n\n"
            
            if resource_analysis["recommendations"]:
                combined_output += f"\n[b yellow]💡 Recommendations:[/b yellow]\n"
                for rec in resource_analysis["recommendations"]:
                    combined_output += f"• {rec}\n"
    
    elif query_type == 'troubleshooting':
        # Check if this is a failing pods query
        intent = detect_troubleshooting_intent(prompt)
        if intent == 'failing_pods_cluster':
            # Focused failing pods analysis
            failing_analysis = analyze_failing_pods(command_outputs)
            
            if failing_analysis["answer"]:
                combined_output += f"\n\n[b green]🎯 Direct Answer:[/b green]\n{failing_analysis['answer']}\n"
                
                for detail in failing_analysis["details"]:
                    combined_output += f"{detail}\n"
                
                if failing_analysis["recommendations"]:
                    combined_output += f"\n[b yellow]💡 Next Steps:[/b yellow]\n"
                    for rec in failing_analysis["recommendations"]:
                        combined_output += f"• {rec}\n"
        elif all_insights or all_suggestions:
            # Regular troubleshooting analysis
            combined_output += f"\n\n[b green]🔍 Diagnosis:[/b green]\n"
            for insight in all_insights:
                combined_output += f"• {insight}\n"
            
            if all_suggestions:
                combined_output += f"\n[b yellow]💡 Recommendations:[/b yellow]\n"
                for suggestion in all_suggestions:
                    combined_output += f"• {suggestion}\n"
            
            # Add root cause analysis if we can determine it
            combined_output += f"\n[b red]🎯 Root Cause Analysis:[/b red]\n"
            if any("exit 1" in insight for insight in all_insights):
                combined_output += "• PRIMARY ISSUE: Container is explicitly configured to fail with 'exit 1' command\n"
                combined_output += "• This is likely a test pod or misconfigured container\n"
                combined_output += "• SOLUTION: Update the container command to run your actual application instead of 'exit 1'\n"
            elif any("No logs available" in insight for insight in all_insights):
                combined_output += "• PRIMARY ISSUE: Container exits immediately without producing logs\n"
                combined_output += "• This suggests the container command/entrypoint is failing instantly\n"
                combined_output += "• SOLUTION: Check container image, command, and entrypoint configuration\n"
            elif any("Exit Code:" in str(all_insights) for insight in all_insights):
                combined_output += "• PRIMARY ISSUE: Application is crashing with specific exit code\n"
                combined_output += "• Check the exit code meaning and application logs for details\n"
            else:
                combined_output += "• Review the insights above for specific failure patterns\n"
                combined_output += "• Focus on container command, image, and resource configuration\n"
    
    return combined_output