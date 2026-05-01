from langchain_core.tools import tool
import os
import requests
import json
from typing import List, Dict, Optional
from kubernetes import client, config
from google.auth import default
from google.auth.transport.requests import Request as GoogleAuthRequest

def _get_k8s_apps_client():
    try:
        config.load_kube_config()
    except:
        try:
            config.load_incluster_config()
        except:
            return None
    return client.AppsV1Api()

def _get_k8s_autoscaling_client():
    try:
        config.load_kube_config()
    except:
        try:
            config.load_incluster_config()
        except:
            return None
    return client.AutoscalingV2Api()

@tool
def optimize_k8s_resources(namespace: str = "default") -> str:
    """
    Performs a multi-dimensional optimization audit of Kubernetes resources.
    Checks: Resource Limits/Requests, Probes (Liveness/Readiness), HPA usage, and Image Tags.
    """
    apps_v1 = _get_k8s_apps_client()
    if not apps_v1:
        return "Error: K8s client configuration failed (check ~/.kube/config)."

    try:
        deployments = apps_v1.list_namespaced_deployment(namespace)
        
        # Try to get HPAs to check coverage
        autoscaling_v2 = _get_k8s_autoscaling_client()
        hpas = []
        if autoscaling_v2:
            try:
                hpas = autoscaling_v2.list_namespaced_horizontal_pod_autoscaler(namespace).items
            except:
                pass
        
        hpa_targets = [h.spec.scale_target_ref.name for h in hpas]
        recommendations = []

        for dep in deployments.items:
            name = dep.metadata.name
            template = dep.spec.template.spec
            containers = template.containers
            
            for container in containers:
                c_name = container.name
                res = container.resources
                issues = []
                
                # 1. Resource Constraints
                if not res or not res.limits or 'cpu' not in res.limits:
                    issues.append("Missing CPU limit")
                if not res or not res.requests or 'memory' not in res.requests:
                    issues.append("Missing Memory request")
                
                # 2. Reliability (Probes)
                if not container.liveness_probe:
                    issues.append("No Liveness Probe")
                if not container.readiness_probe:
                    issues.append("No Readiness Probe")
                
                # 3. Best Practices (Tags)
                if container.image and container.image.endswith(":latest"):
                    issues.append("Using ':latest' tag (unreliable for production)")

                # 4. Scalability (HPA)
                if name not in hpa_targets:
                    issues.append("No HPA configured (manual scaling detected)")

                if issues:
                    recommendations.append(f"**{name}** ({c_name}):\n  - " + "\n  - ".join(issues))

        if not recommendations:
            return f"✅ All deployments in namespace '{namespace}' follow optimization best practices."

        return f"### 🚀 K8s Optimization Audit: {namespace}\n\n" + "\n".join(recommendations)

    except Exception as e:
        return f"K8s Optimization Error: {str(e)}"
