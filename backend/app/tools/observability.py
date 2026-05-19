import json
from langchain_core.tools import tool
import concurrent.futures


@tool
def analyze_heavy_logs(log_content: str, context: str = "") -> str:
    """
    Analyzes large log outputs using Google's Gemini 1.5 Flash directly.
    """
    from app.llm import get_google_sdk_client

    client = get_google_sdk_client()
    if not client:
        from app.llm import get_llm
        llm = get_llm()
        limit = 32000
        truncated_logs = log_content[:limit] + \
            ("...[TRUNCATED]" if len(log_content) > limit else "")
        try:
            res = llm.invoke(
                f"Context: {context}\n\nAnalyze these logs:\n{truncated_logs}")
            return f"Analysis (Standard LLM Fallback):\n{res.content}"
        except Exception as e:
            return f"Error: Google SDK missing and Standard LLM failed: {e}"

    try:
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
def investigate_root_cause(
    service_name: str, owner: str = "my-org", repo: str = "", time_window_minutes: int = 60
) -> str:
    """
    Investigates potential root causes for a service failure by correlating:
    1. Kubernetes Cluster Events
    2. Datadog Alerts
    3. GCP Status
    4. Traefik Ingress Status
    5. Recent Git Commits
    """
    from app.tools import (
        get_cluster_events, get_active_alerts, list_recent_commits,
        check_gcp_status, check_traefik_health, check_azion_status
    )

    if not repo:
        repo = service_name

    report = [
        f"Root Cause Investigation for '{service_name}' (Last {time_window_minutes}m)"]

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_k8s = executor.submit(get_cluster_events.invoke, {
                                     "namespace": "default"})
        future_dd = executor.submit(get_active_alerts.invoke, {
                                    "tags": f"service:{service_name}"})
        future_gcp = executor.submit(check_gcp_status.invoke, {})
        future_traefik = executor.submit(check_traefik_health.invoke, {})
        future_azion = executor.submit(check_azion_status.invoke, {})

        hours = max(1, time_window_minutes // 60)
        future_git = executor.submit(list_recent_commits.invoke, {
                                     "owner": owner, "repo": repo, "hours": hours})

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
            report.append(f"\n[Traefik Ingress]\n{future_traefik.result()}")
        except Exception as e:
            report.append(f"\n[Traefik Ingress] Failed: {e}")

        try:
            report.append(f"\n[Azion Edge Status]\n{future_azion.result()}")
        except Exception as e:
            report.append(f"\n[Azion Edge Status] Failed: {e}")

        try:
            report.append(f"\n[Recent Code Changes]\n{future_git.result()}")
        except Exception as e:
            report.append(f"\n[Recent Code Changes] Failed: {e}")

    full_text = "\n".join(report)

    try:
        summary = analyze_heavy_logs.invoke({
            "log_content": full_text,
            "context": (
                f"Analyze the collected data for service '{service_name}'. "
                "Identify the most probable root cause. "
                "Highlight if it's an Infrastructure (GCP/K8s/Traefik) or Application (Code/Commit) issue."
            )
        })
        return f"{full_text}\n\n====================\n[AI ROOT CAUSE ANALYSIS]\n{summary}"
    except Exception as e:
        return f"{full_text}\n\n[AI Analysis Failed]: {e}"


@tool
def scan_infrastructure() -> str:
    """
    Performs a high-level scan of the entire infrastructure stack.
    Returns a summary of K8s, GCP, Datadog, and Traefik health.
    """
    from app.tools import (
        list_k8s_pods, check_gcp_status, get_active_alerts, check_traefik_health,
        query_gmp_prometheus, check_azion_status
    )
    from app.llm import get_google_sdk_client
    import concurrent.futures

    import datetime

    report = ["Infrastructure Scan Report:"]

    health_data = {
        "timestamp": datetime.datetime.now().isoformat(),
        "k8s": {"status": "unknown", "msg": ""},
        "gcp": {"status": "unknown", "msg": ""},
        "gmp": {"status": "unknown", "msg": ""},
        "datadog": {"status": "unknown", "msg": ""},
        "traefik": {"status": "unknown", "msg": ""},
        "azion": {"status": "unknown", "msg": ""},
        "ai_insight": ""
    }

    raw_scan_results = []

    with concurrent.futures.ThreadPoolExecutor() as executor:
        f_k8s = executor.submit(list_k8s_pods.invoke, {"namespace": "default"})
        f_gcp = executor.submit(check_gcp_status.invoke, {})
        f_gmp = executor.submit(query_gmp_prometheus.invoke, {"query": "up"})
        f_dd = executor.submit(get_active_alerts.invoke, {})
        f_traefik = executor.submit(check_traefik_health.invoke, {})
        f_azion = executor.submit(check_azion_status.invoke, {})

        try:
            k8s_res = f_k8s.result()
            raw_scan_results.append(f"[K8s] {k8s_res}")
            if "Error" in k8s_res and "Running" not in k8s_res:
                report.append("- Kubernetes: 🔴 Issue Detected")
                health_data["k8s"] = {
                    "status": "critical", "msg": k8s_res[:50]}
            else:
                report.append("- Kubernetes: 🟢 Active")
                health_data["k8s"] = {"status": "healthy", "msg": "Active"}
        except Exception as e:
            report.append("- Kubernetes: 🔴 Failed")
            health_data["k8s"] = {"status": "error", "msg": str(e)}

        try:
            gmp_res = f_gmp.result()
            raw_scan_results.append(f"[GMP] {gmp_res}")
            report.append("- GMP: 🟢 Active")
            health_data["gmp"] = {"status": "healthy", "msg": "Active"}
        except Exception as e:
            report.append("- GMP: 🔴 Failed")
            health_data["gmp"] = {"status": "error", "msg": str(e)}

        try:
            gcp_res = f_gcp.result()
            raw_scan_results.append(f"[GCP] {gcp_res}")
            report.append(f"- GCP: {gcp_res}")
            health_data["gcp"] = {"status": "healthy", "msg": "Active"}
        except Exception as e:
            report.append("- GCP: 🔴 Failed")
            health_data["gcp"] = {"status": "error", "msg": str(e)}

        try:
            dd_res = f_dd.result()
            raw_scan_results.append(f"[Datadog] {dd_res}")
            if "No active alerts" in dd_res:
                report.append("- Datadog: 🟢 No alerts")
                health_data["datadog"] = {
                    "status": "healthy", "msg": "No alerts"}
            else:
                report.append("- Datadog: 🟠 Alertas Ativos")
                health_data["datadog"] = {
                    "status": "warning", "msg": "Alerts active"}
        except Exception as e:
            report.append("- Datadog: 🔴 Failed")
            health_data["datadog"] = {"status": "error", "msg": str(e)}

        try:
            tr_res = f_traefik.result()
            raw_scan_results.append(f"[Traefik] {tr_res}")
            if "🟢" in tr_res:
                report.append("- Traefik: 🟢 OK")
                health_data["traefik"] = {"status": "healthy", "msg": "OK"}
            else:
                report.append("- Traefik: 🔴 Issue")
                health_data["traefik"] = {
                    "status": "critical", "msg": "Issue detected"}
        except Exception as e:
            report.append("- Traefik: 🔴 Failed")
            health_data["traefik"] = {"status": "error", "msg": str(e)}

        try:
            azion_res = f_azion.result()
            raw_scan_results.append(f"[Azion] {azion_res}")
            if "🟢" in azion_res:
                report.append("- Azion: 🟢 OK")
                health_data["azion"] = {"status": "healthy", "msg": "OK"}
            else:
                report.append("- Azion: 🔴 Issue")
                health_data["azion"] = {
                    "status": "critical", "msg": "Issue detected"}
        except Exception as e:
            report.append("- Azion: 🔴 Failed")
            health_data["azion"] = {"status": "error", "msg": str(e)}

    ai_summary = "System Normal."
    client = get_google_sdk_client()
    scan_text = "\n".join(raw_scan_results)

    prompt_msgs = [
        "You are a futuristic System Monitor AI.",
        f"SCAN DATA:\n{scan_text}",
        "Provide a ONE-SENTENCE health state summary."
    ]

    try:
        if client:
            response = client.models.generate_content(
                model="gemini-1.5-flash", contents=prompt_msgs)
            ai_summary = response.text.strip()
        else:
            from app.llm import get_llm
            llm = get_llm()
            res = llm.invoke("\n".join(prompt_msgs))
            ai_summary = res.content.strip()
    except Exception:
        ai_summary = "System Normal (AI analysis failed)"

    health_data["ai_insight"] = ai_summary
    report.append(f"\n🧠 **AI Insight:** {ai_summary}")
    report.append(f"\n```json\n{json.dumps(health_data)}\n```")

    return "\n".join(report)


@tool
def correlate_alerts(alerts_input: str = "") -> str:
    """
    Analyzes active alerts to identify patterns.
    """
    from app.llm import get_google_sdk_client
    from app.tools import get_active_alerts

    alerts_data = alerts_input or get_active_alerts.invoke({})
    if "No active alerts" in alerts_data:
        return "No active alerts to correlate."

    prompt = f"Analyze these alerts and find root causes:\n{alerts_data}"
    client = get_google_sdk_client()
    if client:
        try:
            response = client.models.generate_content(
                model="gemini-1.5-flash", contents=prompt)
            return response.text
        except Exception:
            pass

    try:
        from app.llm import get_llm
        llm = get_llm()
        res = llm.invoke(prompt)
        return res.content
    except Exception as e:
        return f"Error: {e}"
