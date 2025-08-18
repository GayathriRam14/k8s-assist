# workflows.py - Predefined troubleshooting workflows

# Predefined troubleshooting workflows
TROUBLESHOOTING_WORKFLOWS = {
    "pod_not_running": [
        "kubectl get pod {pod_name} -n {namespace} -o wide",
        "kubectl describe pod {pod_name} -n {namespace}",
        "kubectl get events -n {namespace} --field-selector involvedObject.name={pod_name}",
        "kubectl logs {pod_name} -n {namespace} --tail=50"
    ],
    "pod_crashing": [
        "kubectl get pod {pod_name} -n {namespace} -o wide",
        "kubectl describe pod {pod_name} -n {namespace}",
        "kubectl logs {pod_name} -n {namespace} --tail=100",
        "kubectl logs {pod_name} -n {namespace} --previous --tail=50",
        "kubectl get events -n {namespace} --field-selector involvedObject.name={pod_name}"
    ],
    "service_issues": [
        "kubectl get svc -n {namespace}",
        "kubectl describe svc {service_name} -n {namespace}",
        "kubectl get endpoints -n {namespace}",
        "kubectl get pods -n {namespace} -o wide --show-labels"
    ],
    "deployment_issues": [
        "kubectl get deployment {deployment_name} -n {namespace} -o wide",
        "kubectl describe deployment {deployment_name} -n {namespace}",
        "kubectl get rs -n {namespace}",
        "kubectl get pods -n {namespace} -l app={deployment_name}"
    ],
    "resource_usage": [
        "kubectl top pods -n {namespace}",
        "kubectl top nodes",
        "kubectl describe nodes"
    ],
    "failing_pods_cluster": [
        "kubectl get pods --all-namespaces --field-selector=status.phase!=Running",
        "kubectl get pods --all-namespaces -o wide | grep -E '(Error|Failed|CrashLoopBackOff|ImagePullBackOff|Pending)'",
        "kubectl get events --all-namespaces --sort-by='.firstTimestamp' | grep -E '(Warning|Error)' | tail -20"
    ],
    "cluster_assessment": [
        "kubectl get nodes -o wide",
        "kubectl get pods --all-namespaces | grep -v Running",
        "kubectl get events --all-namespaces --sort-by='.firstTimestamp' | tail -20",
        "kubectl top nodes",
        "kubectl get pods --all-namespaces -o wide",
        "kubectl get services --all-namespaces",
        "kubectl get pv",
        "kubectl get storageclass"
    ],
    "node_assessment": [
        "kubectl get nodes -o wide",
        "kubectl describe nodes",
        "kubectl top nodes",
        "kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{\"\\t\"}{.status.conditions[?(@.type==\"Ready\")].status}{\"\\t\"}{.status.conditions[?(@.type==\"Ready\")].reason}{\"\\n\"}{end}'",
        "kubectl get events --all-namespaces --field-selector source=node-controller",
        "kubectl get pods --all-namespaces --field-selector spec.nodeName!='' -o wide"
    ]
}