from langchain_core.tools import tool
import os
import json
from typing import List, Dict, Optional

try:
    from kubernetes import client, config
except ImportError:
    client = None
    config = None

def _get_k8s_apps_client():
    if not config:
        return None
    try:
        config.load_kube_config()
    except:
        try:
            config.load_incluster_config()
        except:
            return None
    return client.AppsV1Api()

@tool
def optimize_k8s_resources(namespace: str = "default", dry_run: bool = True) -> str:
    """
    Analyzes Kubernetes deployments in a namespace for resource optimization.
    Checks for missing CPU/Memory limits and requests, and suggests 'right-sizing'.
    If dry_run is False, it could potentially apply recommendations (not implemented for safety).
    """
    apps_v1 = _get_k8s_apps_client()
    if not apps_v1:
        return "Error: Kubernetes client unavailable. Use Mock tools or check configuration."

    try:
        deployments = apps_v1.list_namespaced_deployment(namespace)
        recommendations = []

        for dep in deployments.items:
            name = dep.metadata.name
            containers = dep.spec.template.spec.containers
            
            for container in containers:
                c_name = container.name
                resources = container.resources
                
                # Check for missing limits/requests
                issues = []
                if not resources.limits or 'cpu' not in resources.limits:
                    issues.append("Missing CPU limit")
                if not resources.limits or 'memory' not in resources.limits:
                    issues.append("Missing Memory limit")
                if not resources.requests or 'cpu' not in resources.requests:
                    issues.append("Missing CPU request")
                
                if issues:
                    recommendations.append(
                        f"- Deployment '{name}' (Container: {c_name}): {', '.join(issues)}. "
                        "Recommendation: Add standard resource constraints (e.g., 100m CPU, 128Mi RAM)."
                    )
                else:
                    # Right-sizing suggestion (Simulated)
                    recommendations.append(
                        f"- Deployment '{name}' (Container: {c_name}): Resources are configured. "
                        "Recommendation: Monitor usage via Datadog to confirm if '250m CPU' can be reduced to '100m'."
                    )

        if not recommendations:
            return f"No deployments found in namespace '{namespace}' or all are perfectly optimized."

        header = f"### 🚀 K8s Resource Optimization Report (Namespace: {namespace})\n"
        if dry_run:
            header += "*Note: This is a diagnostic analysis (Dry Run).*\n\n"
        
        return header + "\n".join(recommendations)

    except Exception as e:
        return f"Error during optimization analysis: {str(e)}"
