from langchain_core.tools import tool
from typing import List, Dict

@tool
def list_k8s_pods(namespace: str = "default") -> str:
    """Lists all pods in the specified Kubernetes namespace."""
    # Mock implementation
    if namespace == "default":
        # Simulate a crashing frontend pod
        return "Pods in default: [frontend-7d6f (CrashLoopBackOff), backend-9s8d (Running), db-postgres-1a2b (Running)]"
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
        # Simulate a database connection error in the logs
        return (
            f"Name: {pod_name}\n"
            "Status: CrashLoopBackOff\n"
            "Restarts: 5\n"
            "Events: Back-off restarting failed container\n"
            "Logs:\n"
            "[INFO] Starting server...\n"
            "[ERROR] ConnectionRefusedError: POST https://postgres-db:5432 - Connection refused\n"
            "[FATAL] Unable to connect to database. Exiting."
        )
    return f"Pod {pod_name} not found."

@tool
def check_gcp_status(service: str = "compute") -> str:
    """Checks the status of Google Cloud Platform services."""
    # Simulate maintenance mode for Cloud SQL
    if "sql" in service.lower() or "db" in service.lower() or "postgres" in service.lower():
        return "GCP Service Cloud SQL (postgres-db) is in MAINTENANCE mode. Scheduled update in progress."
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
