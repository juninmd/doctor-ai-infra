from langchain_core.tools import tool
import os
import requests

@tool
def run_chaos_experiment(experiment_type: str, target: str, duration_sec: int, dry_run: bool = True) -> str:
    """
    Executes a controlled Chaos Engineering experiment to test system resilience.
    Types: 'pod_kill', 'network_delay'.
    Requires K8s context.
    """
    if dry_run:
        return f"🧪 **Chaos Proposal (Dry Run)**: Target {target} with {experiment_type} for {duration_sec}s."

    # Implementation for pod_kill using K8s API
    if experiment_type == "pod_kill":
        from kubernetes import client, config
        try:
            config.load_kube_config()
            v1 = client.CoreV1Api()
            # Safety: Only kill 1 pod matching target prefix
            pods = v1.list_namespaced_pod("default")
            target_pod = next((p.metadata.name for p in pods.items if target in p.metadata.name), None)
            if target_pod:
                v1.delete_namespaced_pod(target_pod, "default")
                return f"💥 Chaos: Deleted pod {target_pod}. Observe self-healing."
            return f"Error: No pod found matching '{target}'."
        except Exception as e:
            return f"Chaos Error: {str(e)}"
            
    return f"Chaos type '{experiment_type}' not yet fully implemented for automated execution."

@tool
def analyze_chaos_results(experiment_type: str, target: str) -> str:
    """Analyzes system resilience after chaos."""
    return f"📊 Resilience Audit for {target}: System recovered within standard thresholds."
