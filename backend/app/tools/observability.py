from langchain_core.tools import tool
import concurrent.futures
import json

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
        # Fallback for Ollama or if SDK is not configured
        # This ensures "Ollama compatibility" as requested
        from app.llm import get_llm
        llm = get_llm()

        # Truncate for smaller context windows common in local models
        # 32k chars is roughly 8k tokens, safe for Llama 3
        limit = 32000
        truncated_logs = log_content[:limit] + ("...[TRUNCATED]" if len(log_content) > limit else "")

        try:
            res = llm.invoke(f"Context: {context}\n\nAnalyze these logs:\n{truncated_logs}")
            return f"Analysis (Standard LLM Fallback):\n{res.content}"
        except Exception as e:
            return f"Error: Google SDK missing and Standard LLM failed: {e}"

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

    full_text = "\n".join(report)

    # Always perform AI analysis for root cause correlation (Best Agent behavior)
    try:
        summary = analyze_heavy_logs.invoke({
            "log_content": full_text,
            "context": (
                f"Analyze the collected data for service '{service_name}'. "
                "Identify the most probable root cause. "
                "Assign a probability score (0-100%) to your findings. "
                "Highlight if it's an Infrastructure (GCP/K8s), Application (Code/Commit), or External (Azion) issue."
            )
        })
        return f"{full_text}\n\n====================\n[AI ROOT CAUSE ANALYSIS]\n{summary}"
    except Exception as e:
        return f"{full_text}\n\n[AI Analysis Failed]: {e}"

@tool
def scan_infrastructure() -> str:
    """
    Performs a high-level scan of the entire infrastructure stack.
    Returns a summary of K8s, GCP, Datadog, and Azion health.
    Useful for initial triage.
    """
    from app.tools import (
        list_k8s_pods, check_gcp_status, get_active_alerts, check_azion_edge,
        query_gmp_prometheus
    )
    from app.llm import get_google_sdk_client
    import concurrent.futures
    import json
    import datetime

    report = ["Infrastructure Scan Report:"]

    # Data for structured output
    health_data = {
        "timestamp": datetime.datetime.now().isoformat(),
        "k8s": {"status": "unknown", "msg": ""},
        "gcp": {"status": "unknown", "msg": ""},
        "gmp": {"status": "unknown", "msg": ""},
        "datadog": {"status": "unknown", "msg": ""},
        "azion": {"status": "unknown", "msg": ""},
        "ai_insight": ""
    }

    raw_scan_results = []

    with concurrent.futures.ThreadPoolExecutor() as executor:
        f_k8s = executor.submit(list_k8s_pods.invoke, {"namespace": "default"})
        f_gcp = executor.submit(check_gcp_status.invoke, {})
        f_gmp = executor.submit(query_gmp_prometheus.invoke, {"query": "up"})
        f_dd = executor.submit(get_active_alerts.invoke, {}) # All alerts
        f_azion = executor.submit(check_azion_edge.invoke, {}) # All apps

        try:
            k8s_res = f_k8s.result()
            raw_scan_results.append(f"[K8s] {k8s_res}")
            # Crude analysis of the string output
            if "Error" in k8s_res and not "Running" in k8s_res:
                report.append(f"- Kubernetes: 🔴 Issue Detected ({k8s_res[:100]}...)")
                health_data["k8s"] = {"status": "critical", "msg": k8s_res[:50]}
            else:
                pod_count = k8s_res.count("Running") if "Running" in k8s_res else "Unknown"
                report.append(f"- Kubernetes: 🟢 Active ({pod_count} Pods Running)")
                health_data["k8s"] = {"status": "healthy", "msg": f"{pod_count} pods running"}
        except Exception as e:
            report.append(f"- Kubernetes: 🔴 Check Failed ({str(e)})")
            health_data["k8s"] = {"status": "error", "msg": str(e)}

        try:
            gcp_res = f_gcp.result()
            raw_scan_results.append(f"[GCP] {gcp_res}")
            report.append(f"- GCP: {gcp_res}")
            health_data["gcp"] = {"status": "healthy", "msg": "Active"} # Simplified
        except Exception as e:
            report.append(f"- GCP: 🔴 Check Failed ({str(e)})")
            health_data["gcp"] = {"status": "error", "msg": str(e)}

        try:
            gmp_res = f_gmp.result()
            raw_scan_results.append(f"[GMP] {gmp_res}")
            if "Error" in gmp_res:
                report.append(f"- GMP: 🔴 Check Failed ({gmp_res[:50]}...)")
                health_data["gmp"] = {"status": "critical", "msg": gmp_res[:50]}
            else:
                report.append(f"- GMP: 🟢 Active (Prometheus Query Successful)")
                health_data["gmp"] = {"status": "healthy", "msg": "Query OK"}
        except Exception as e:
            report.append(f"- GMP: 🔴 Check Failed ({str(e)})")
            health_data["gmp"] = {"status": "error", "msg": str(e)}

        try:
            dd_res = f_dd.result()
            raw_scan_results.append(f"[Datadog] {dd_res}")
            if "No active alerts" in dd_res:
                 report.append(f"- Datadog: 🟢 No active alerts")
                 health_data["datadog"] = {"status": "healthy", "msg": "No alerts"}
            else:
                alert_count = dd_res.count("[Alert]")
                report.append(f"- Datadog: 🟠 {alert_count} Active Alerts")
                health_data["datadog"] = {"status": "warning", "msg": f"{alert_count} alerts"}
        except Exception as e:
             report.append(f"- Datadog: 🔴 Check Failed ({str(e)})")
             health_data["datadog"] = {"status": "error", "msg": str(e)}

        try:
            az_res = f_azion.result()
            raw_scan_results.append(f"[Azion] {az_res}")
            if "Active" in az_res:
                 # Check if we can parse the count
                 count = az_res.count("id") if "id" in az_res else "Multiple"
                 report.append(f"- Azion: 🟢 Edge Active")
                 health_data["azion"] = {"status": "healthy", "msg": "Edge Active"}
            else:
                 report.append(f"- Azion: 🟠 {az_res[:100]}")
                 health_data["azion"] = {"status": "warning", "msg": az_res[:50]}
        except Exception as e:
             report.append(f"- Azion: 🔴 Check Failed ({str(e)})")
             health_data["azion"] = {"status": "error", "msg": str(e)}

    # AI Insight Generation (The "Intelligence" Layer)
    ai_summary = "System Normal."
    client = get_google_sdk_client()
    scan_text = "\n".join(raw_scan_results)

    if client:
        try:
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=[
                    "You are a futuristic System Monitor AI.",
                    "Analyze the following infrastructure scan results.",
                    "Provide a ONE-SENTENCE, punchy, executive summary of the health state.",
                    "If everything is fine, say something witty and positive.",
                    "If there are issues, pinpoint the most critical one immediately.",
                    f"SCAN DATA:\n{scan_text}"
                ]
            )
            ai_summary = response.text.strip()
        except Exception:
            # Silent fallback
            pass

    health_data["ai_insight"] = ai_summary
    report.append(f"\n🧠 **AI Insight:** {ai_summary}")

    # Append hidden JSON block for frontend integration
    report.append(f"\n```json\n{json.dumps(health_data)}\n```")

    return "\n".join(report)
