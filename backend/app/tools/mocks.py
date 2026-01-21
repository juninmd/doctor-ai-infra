from langchain.tools import tool
from typing import List, Dict

@tool
def list_pods(namespace: str = "default") -> List[Dict]:
    """List pods in a Kubernetes namespace."""
    # Mock implementation
    return [
        {"name": "frontend-prod-123", "status": "Running", "restarts": 0},
        {"name": "backend-api-456", "status": "CrashLoopBackOff", "restarts": 5},
        {"name": "db-redis-789", "status": "Running", "restarts": 0}
    ]

@tool
def describe_pod(pod_name: str, namespace: str = "default") -> str:
    """Get detailed status of a pod."""
    if "backend-api" in pod_name:
        return "Events: Back-off restarting failed container. Error: ConnectionRefusedError connecting to Redis."
    return "Status: Running. Ready: 1/1."

@tool
def check_vm_status(instance_name: str, zone: str = "us-central1-a") -> str:
    """Check GCP VM status."""
    return "RUNNING"

@tool
def get_dd_metrics(query: str) -> Dict:
    """Get metrics from Datadog."""
    return {"metric": "system.cpu.idle", "points": [[1700000000, 95.5], [1700000060, 20.1]]}

@tool
def check_azion_edge_function(function_id: str) -> str:
    """Check status of Azion Edge Function."""
    return "Active"
