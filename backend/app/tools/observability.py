from langchain_core.tools import tool

@tool
def investigate_root_cause(service_name: str, owner: str = "my-org", repo: str = "", time_window_minutes: int = 60) -> str:
    """
    Investigates potential root causes for a service failure by correlating:
    1. Kubernetes Cluster Events (last N events)
    2. Datadog Alerts
    3. Recent Git Commits (if repo provided)

    Args:
        service_name: Name of the service to investigate.
        owner: GitHub Organization (default: my-org).
        repo: GitHub Repository Name (optional, defaults to service_name if empty).
        time_window_minutes: How far back to look (default 60).
    """
    # Import here to respect the global USE_REAL_TOOLS switch and avoid circular dependency
    # This imports from app.tools.__init__, which selects real/mock based on env var
    from app.tools import get_cluster_events, get_active_alerts, list_recent_commits

    if not repo:
        repo = service_name

    report = [f"Root Cause Investigation for '{service_name}' (Last {time_window_minutes}m)"]

    # 1. Kubernetes Events
    try:
        k8s_events = get_cluster_events.invoke({"namespace": "default"})
        report.append(f"\n[Kubernetes Events]\n{k8s_events}")
    except Exception as e:
        report.append(f"\n[Kubernetes Events] Failed: {e}")

    # 2. Datadog Alerts
    try:
        dd_alerts = get_active_alerts.invoke({"tags": f"service:{service_name}"})
        report.append(f"\n[Datadog Alerts]\n{dd_alerts}")
    except Exception as e:
        report.append(f"\n[Datadog Alerts] Failed: {e}")

    # 3. Git Commits
    try:
        hours = max(1, time_window_minutes // 60)
        commits = list_recent_commits.invoke({"owner": owner, "repo": repo, "hours": hours})
        report.append(f"\n[Recent Code Changes]\n{commits}")
    except Exception as e:
        report.append(f"\n[Recent Code Changes] Failed: {e}")

    return "\n".join(report)
