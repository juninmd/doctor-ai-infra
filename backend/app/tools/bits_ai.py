from langchain_core.tools import tool


@tool
def bits_ai_investigate_monitor(
        monitor_query: str,
        service_name: str = "") -> str:
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
        alerts = get_active_alerts.invoke(
            {"tags": f"service:{service_name}" if service_name else ""})

        # 2. Optionally fetch logs if a service is specified
        logs = ""
        if service_name:
            try:
                logs = get_pod_logs.invoke(
                    {"pod_name": service_name, "namespace": "default", "lines": 20})
            except BaseException:
                logs = "Log fetch failed or skipped."

        # 3. Generate initial hypotheses
        hypothesis_prompt = (
            f"You are Bits AI, an expert Datadog SRE Copilot.\n"
            f"Given the monitor query: '{monitor_query}'\n"
            f"Alerts: {alerts}\nMetrics: {metrics}\nLogs: {logs}\n"
            f"Formulate 3 distinct hypotheses for the root cause."
        )
        hypotheses = generate_diagnosis(
            prompt=hypothesis_prompt,
            system_instruction="You are an expert SRE log analyzer."
        )

        # 4. Evaluate and generate deep sub-hypotheses/diagnosis
        deep_prompt = (
            f"You are Bits AI, using an iterative branching hypothesis strategy.\n"
            f"Based on the data:\nAlerts: {alerts}\nMetrics: {metrics}\nLogs: {logs}\n\n"
            f"And these initial hypotheses:\n{hypotheses}\n\n"
            f"Test and validate each hypothesis. Break down the most likely one into sub-hypotheses, "
            f"and follow the evidence to determine the true root cause. Then suggest remediation."
        )
        diagnosis = generate_diagnosis(
            prompt=deep_prompt,
            system_instruction="You are an expert Datadog copilot using branching logic."
        )

        return (
            f"### 🐶 Bits AI SRE Copilot Investigation\n\n"
            f"**Query:** {monitor_query}\n\n"
            f"**Initial Hypotheses:**\n{hypotheses}\n\n"
            f"**Deep Investigation & Root Cause:**\n{diagnosis}"
        )

    except Exception as e:
        return f"Error executing Bits AI workflow: {e}"

# Verified implementation per documentation
