from langchain_core.tools import tool
import concurrent.futures

@tool
def investigate_root_cause(service_name: str, owner: str = "my-org", repo: str = "", time_window_minutes: int = 60) -> str:
    """
    Investigates potential root causes for a service failure by correlating:
    1. Kubernetes Cluster Events
    2. Datadog Alerts
    3. GCP Status
    4. Azion Edge Status
    5. Recent Git Commits

    Args:
        service_name: Name of the service to investigate.
        owner: GitHub Organization (default: my-org).
        repo: GitHub Repository Name (optional, defaults to service_name if empty).
        time_window_minutes: How far back to look (default 60).
    """
    # Import here to respect the global USE_REAL_TOOLS switch and avoid circular dependency
    from app.tools import (
        get_cluster_events, get_active_alerts, list_recent_commits,
        check_gcp_status, check_azion_edge
    )

    if not repo:
        repo = service_name

    report = [f"Root Cause Investigation for '{service_name}' (Last {time_window_minutes}m)"]

    # Parallel execution for speed (Best 2026 performance)
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Define tasks with invoke
        future_k8s = executor.submit(get_cluster_events.invoke, {"namespace": "default"})
        future_dd = executor.submit(get_active_alerts.invoke, {"tags": f"service:{service_name}"})
        future_gcp = executor.submit(check_gcp_status.invoke, {})
        future_azion = executor.submit(check_azion_edge.invoke, {"domain": service_name})

        hours = max(1, time_window_minutes // 60)
        future_git = executor.submit(list_recent_commits.invoke, {"owner": owner, "repo": repo, "hours": hours})

        # Collect results
        try:
            report.append(f"\n[Kubernetes Events]\n{future_k8s.result()}")
        except Exception as e:
            report.append(f"\n[Kubernetes Events] Failed: {e}")

        try:
            report.append(f"\n[Datadog Alerts]\n{future_dd.result()}")
        except Exception as e:
            report.append(f"\n[Datadog Alerts] Failed: {e}")

        try:
            report.append(f"\n[GCP Status]\n{future_gcp.result()}")
        except Exception as e:
            report.append(f"\n[GCP Status] Failed: {e}")

        try:
            report.append(f"\n[Azion Edge]\n{future_azion.result()}")
        except Exception as e:
            report.append(f"\n[Azion Edge] Failed: {e}")

        try:
            report.append(f"\n[Recent Code Changes]\n{future_git.result()}")
        except Exception as e:
            report.append(f"\n[Recent Code Changes] Failed: {e}")

    return "\n".join(report)

@tool
def scan_infrastructure() -> str:
    """
    Performs a high-level scan of the entire infrastructure stack.
    Returns a summary of K8s, GCP, Datadog, and Azion health.
    Useful for initial triage.
    """
    from app.tools import (
        list_k8s_pods, check_gcp_status, get_active_alerts, check_azion_edge
    )

    report = ["Infrastructure Scan Report:"]

    with concurrent.futures.ThreadPoolExecutor() as executor:
        f_k8s = executor.submit(list_k8s_pods.invoke, {"namespace": "default"})
        f_gcp = executor.submit(check_gcp_status.invoke, {})
        f_dd = executor.submit(get_active_alerts.invoke, {}) # All alerts
        f_azion = executor.submit(check_azion_edge.invoke, {}) # All apps

        try:
            k8s_res = f_k8s.result()
            # Crude analysis of the string output
            count = k8s_res.count("Running") if "Running" in k8s_res else 0
            if "Error" in k8s_res and not "Running" in k8s_res:
                report.append(f"- Kubernetes: 🔴 Issue Detected ({k8s_res})")
            else:
                report.append(f"- Kubernetes: 🟢 Active (Found 'Running' pods)")
        except Exception as e:
            report.append(f"- Kubernetes: 🔴 Check Failed ({e})")

        try:
            report.append(f"- GCP: {f_gcp.result()}")
        except Exception as e:
            report.append(f"- GCP: 🔴 Check Failed ({e})")

        try:
            dd_res = f_dd.result()
            if "No active alerts" in dd_res:
                 report.append(f"- Datadog: 🟢 No active alerts")
            else:
                alert_count = dd_res.count("[Alert]")
                report.append(f"- Datadog: 🟠 {alert_count} Active Alerts")
        except Exception as e:
             report.append(f"- Datadog: 🔴 Check Failed ({e})")

        try:
            az_res = f_azion.result()
            if "Active" in az_res:
                 report.append(f"- Azion: 🟢 {az_res}")
            else:
                 report.append(f"- Azion: 🟠 {az_res}")
        except Exception as e:
             report.append(f"- Azion: 🔴 Check Failed ({e})")

    return "\n".join(report)

@tool
def analyze_heavy_logs(log_content: str, context: str = "") -> str:
    """
    Analyzes large log outputs using Google's Gemini 1.5 Flash directly (bypassing standard context limits).
    Ideal for troubleshooting complex stack traces or multi-service logs.

    Args:
        log_content: The raw log text to analyze.
        context: Optional context about what we are looking for (e.g., "Find database connection errors").
    """
    from app.llm import get_google_sdk_client

    client = get_google_sdk_client()
    if not client:
        return "Error: Google Gen AI SDK not configured (missing key or library). Use standard analysis."

    try:
        # Direct generation using the native SDK
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=[
                "You are an expert SRE log analyzer.",
                f"Context: {context}",
                "Analyze the following logs and find the root cause of errors. Be technical and concise.",
                log_content
            ]
        )
        return f"Gemini Analysis:\n{response.text}"
    except Exception as e:
        return f"Error analyzing logs with Gemini SDK: {e}"
