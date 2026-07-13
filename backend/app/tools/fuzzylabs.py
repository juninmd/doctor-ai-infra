from langchain_core.tools import tool


@tool
def fuzzylabs_sre_workflow(service_name: str, log_group: str = "", slack_channel: str = "#incidents") -> str:
    """
    Reads error logs (from CloudWatch/K8s), inspects source code via GitHub integration,
    produces a diagnosis/fix suggestion, and sends the results to Slack.
    This mimics the functionality of the FuzzyLabs SRE Agent.

    Args:
        service_name: The name of the service to analyze.
        log_group: The CloudWatch log group or similar identifier.
        slack_channel: The Slack channel to send the report to.
    """
    from app.tools import get_pod_logs, list_recent_commits, send_slack_notification

    try:
        # 1. Read error logs
        # Assuming namespace 'default' for simplicity
        logs = get_pod_logs.invoke({"pod_name": service_name, "namespace": "default", "lines": 50})

        # 2. Inspect source code / recent commits
        commits = list_recent_commits.invoke({"owner": "my-org", "repo": service_name, "hours": 24})

        # 3. Produce diagnosis and fix suggestions
        prompt = (
            f"You are the FuzzyLabs SRE Agent.\n"
            f"Analyze the following logs and recent commits to identify the root cause "
            f"of the issue in '{service_name}' and suggest a fix.\n\n"
            f"Logs:\n{logs}\n\n"
            f"Recent Commits:\n{commits}"
        )

        from app.llm import generate_diagnosis
        diagnosis = generate_diagnosis(prompt=prompt)

        # 4. Send results to Slack
        report_message = f"🚨 *FuzzyLabs SRE Agent Diagnosis for {service_name}* 🚨\n\n{diagnosis}"
        slack_result = send_slack_notification.invoke({"channel": slack_channel, "message": report_message})

        return (
            f"### 🕵️‍♀️ FuzzyLabs SRE Agent Workflow Complete\n\n"
            f"**Diagnosis & Suggested Fix:**\n{diagnosis}\n\n"
            f"**Notification Status:**\n{slack_result}"
        )

    except Exception as e:
        return f"Error executing FuzzyLabs SRE workflow: {e}"
