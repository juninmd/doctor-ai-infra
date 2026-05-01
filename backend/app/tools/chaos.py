from langchain_core.tools import tool

@tool
def run_chaos_experiment(experiment_type: str, target: str, duration_sec: int, dry_run: bool = True) -> str:
    """
    Executes a controlled Chaos Engineering experiment to test system resilience.
    Types: 'pod_kill' (randomly terminates pods), 'network_delay' (injects 500ms latency), 'cpu_stress' (spikes CPU).
    WARNING: Highly destructive. Always use dry_run=True first.
    """
    if dry_run:
        return (
            f"🧪 **[DRY RUN] Chaos Experiment Proposal**\n"
            f"- **Type**: {experiment_type}\n"
            f"- **Target**: {target}\n"
            f"- **Duration**: {duration_sec} seconds\n"
            f"- **Expected Outcome**: Kubernetes should automatically spin up new pods or route traffic to healthy nodes.\n"
            f"Execute with `dry_run=False` to unleash chaos."
        )
    
    # In a real scenario, this integrates with Chaos Mesh or Gremlin
    return (
        f"💥 **CHAOS INJECTED** 💥\n"
        f"Experiment '{experiment_type}' is now running on '{target}' for {duration_sec}s.\n"
        f"Use `analyze_chaos_results` after the duration to verify system resilience."
    )

@tool
def analyze_chaos_results(experiment_type: str, target: str) -> str:
    """
    Analyzes metrics and logs after a chaos experiment to determine if the system survived gracefully.
    """
    if experiment_type == "pod_kill":
        return (
            f"📊 **Chaos Report: {experiment_type} on {target}**\n"
            "- **Resilience Score**: 95/100 (Excellent)\n"
            "- **Observation**: 3 pods were killed. ReplicaSet controller detected termination within 2 seconds. New pods were Ready in 8 seconds. Overall error rate during chaos was < 0.01%.\n"
            "- **Conclusion**: System is highly resilient to random pod failures."
        )
    elif experiment_type == "network_delay":
         return (
            f"📊 **Chaos Report: {experiment_type} on {target}**\n"
            "- **Resilience Score**: 40/100 (Warning)\n"
            "- **Observation**: Injected 500ms latency. The upstream service 'frontend-web' experienced cascaded timeouts because its client timeout is hardcoded to 300ms.\n"
            "- **Conclusion**: **VULNERABILITY DETECTED**. Route to Code_Specialist to increase client timeouts and implement circuit breakers."
        )
    
    return "Chaos results being compiled..."
