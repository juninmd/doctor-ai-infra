from langchain_core.tools import tool
import os

@tool
def bits_ai_investigate_monitor(monitor_query: str, service_name: str = "") -> str:
    """
    Mimics the functionality of Datadog Bits AI.
    It takes a monitor query or active alerts, correlates them with logs and metrics,
    and uses the LLM to summarize the incident and suggest remediations.

    Args:
        monitor_query: The query or description of the alert to investigate.
        service_name: The optional name of the service to focus on.
    """
    from app.tools import get_datadog_metrics, get_active_alerts, get_pod_logs
    from app.llm import generate_diagnosis

    try:
        # 1. Fetch relevant metrics and alerts
        metrics = get_datadog_metrics.invoke({"query": monitor_query})
        alerts = get_active_alerts.invoke({"tags": f"service:{service_name}" if service_name else ""})

        # 2. Optionally fetch logs if a service is specified
        logs = ""
        if service_name:
             try:
                 logs = get_pod_logs.invoke({"pod_name": service_name, "namespace": "default", "lines": 20})
             except:
                 logs = "Log fetch failed or skipped."

        # 3. Formulate the prompt for the Copilot
        prompt = (
            f"You are Bits AI, an expert Datadog SRE Copilot.\n"
            f"Investigate the following monitor query: '{monitor_query}'\n\n"
            f"Active Alerts:\n{alerts}\n\n"
            f"Related Metrics:\n{metrics}\n\n"
            f"Recent Logs (if any):\n{logs}\n\n"
            f"Please analyze the situation, identify the root cause, and suggest remediation steps."
        )

        # 4. Generate diagnosis using the AI Copilot
        diagnosis = generate_diagnosis(prompt=prompt, system_instruction="You are an expert SRE log analyzer and Datadog copilot.")

        return (
            f"### 🐶 Bits AI SRE Copilot Investigation\n\n"
            f"**Query:** {monitor_query}\n\n"
            f"{diagnosis}"
        )

    except Exception as e:
        return f"Error executing Bits AI workflow: {e}"
