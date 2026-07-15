from langchain_core.tools import tool
import os

@tool
def incidentfox_auto_investigate(incident_context: str, service_name: str = "unknown") -> str:
    """
    Mimics the functionality of IncidentFox's automated Slack incident response.
    It triggers an automated investigation across infrastructure and logs,
    generates a root cause summary, and formats it for Slack/Chat-first debugging.

    Args:
        incident_context: The raw alert data or context about the incident.
        service_name: The name of the affected service (if known).
    """
    from app.tools import investigate_root_cause, send_slack_notification
    from app.llm import generate_diagnosis

    try:
        # 1. Run the deeper infrastructure root cause investigation
        # Using a shorter time window for immediate response
        investigation_data = investigate_root_cause.invoke({
            "service_name": service_name,
            "time_window_minutes": 30
        })

        # 2. Formulate the prompt for IncidentFox AI
        prompt = (
            f"You are IncidentFox, an autonomous AI SRE.\n"
            f"You have been triggered by the following alert context: '{incident_context}'\n\n"
            f"Investigation Results:\n{investigation_data}\n\n"
            f"Please provide a concise root cause summary, alert correlation analysis, "
            f"and the recommended next steps. Format it nicely for a Slack message."
        )

        # 3. Generate the summary using the AI Copilot
        summary = generate_diagnosis(prompt=prompt, system_instruction="You are an expert autonomous Incident Response AI.")

        # 4. Dispatch the report to Slack
        report_message = f"🦊 *IncidentFox Auto-Investigation: {service_name}* 🦊\n\n{summary}"
        slack_result = send_slack_notification.invoke({"channel": "#incidents", "message": report_message})

        return (
            f"### 🦊 IncidentFox Auto-Investigation Complete\n\n"
            f"{summary}\n\n"
            f"**Notification Status:**\n{slack_result}"
        )

    except Exception as e:
        return f"Error executing IncidentFox workflow: {e}"
