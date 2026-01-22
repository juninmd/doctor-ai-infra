from langchain_core.tools import tool
from typing import List, Dict

@tool
def list_k8s_pods(namespace: str = "default") -> str:
    """Lists all pods in the specified Kubernetes namespace."""
    # Mock implementation
    if namespace == "default":
        return "Pods in default: [frontend-7d6f, backend-9s8d, db-postgres-1a2b]"
    elif namespace == "kube-system":
        return "Pods in kube-system: [coredns-1, coredns-2, kube-proxy-x, etcd-0]"
    return f"No pods found in namespace {namespace}."

@tool
def describe_pod(pod_name: str) -> str:
    """Describes a specific pod to get details about its status and events."""
    # Mock implementation
    if "backend" in pod_name:
        return f"Name: {pod_name}\nStatus: Running\nRestarts: 0\nEvents: Pulled image successfully."
    elif "frontend" in pod_name:
        return f"Name: {pod_name}\nStatus: CrashLoopBackOff\nRestarts: 5\nEvents: Back-off restarting failed container."
    return f"Pod {pod_name} not found."

@tool
def check_gcp_status(service: str = "compute") -> str:
    """Checks the status of Google Cloud Platform services."""
    return f"GCP Service {service} is OPERATIONAL. No incidents reported."

@tool
def query_gmp_prometheus(query: str) -> str:
    """Queries Google Managed Prometheus (GMP) for metrics."""
    return f"GMP Query '{query}' returned: cpu_usage=0.45"

@tool
def get_datadog_metrics(query: str) -> str:
    """Queries Datadog for specific metrics."""
    return f"Datadog Metric for '{query}': Avg 45ms latency, 99.9% availability."

@tool
def check_azion_edge(domain: str) -> str:
    """Checks the status of an Azion Edge Application."""
    return f"Azion Edge for {domain}: Cache Hit Ratio 85%, Status Active."
