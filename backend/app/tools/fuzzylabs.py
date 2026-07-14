from langchain_core.tools import tool
import os

@tool
def fuzzylabs_sre_workflow(service_name: str, log_group: str = "", slack_channel: str = "#incidents", namespace: str = "default", owner: str = "my-org", repo: str = None) -> str:
    """
    Reads error logs (from CloudWatch/K8s), inspects source code via GitHub integration,
    produces a diagnosis/fix suggestion, and sends the results to Slack.
    This mimics the functionality of the FuzzyLabs SRE Agent.

    Args:
        service_name: The name of the service to analyze.
        log_group: The CloudWatch log group or similar identifier.
        slack_channel: The Slack channel to send the report to.
        namespace: The Kubernetes namespace to fetch logs from.
        owner: The GitHub repository owner.
        repo: The GitHub repository name. Defaults to service_name if not provided.
    """
    from app.tools import get_pod_logs, list_recent_commits, send_slack_notification
    from app.llm import get_google_sdk_client, get_llm

    try:
        # 1. Read error logs
        logs = get_pod_logs.invoke({"pod_name": service_name, "namespace": namespace, "lines": 50})

        # 2. Inspect source code / recent commits
        repo_name = repo if repo else service_name
        commits = list_recent_commits.invoke({"owner": owner, "repo": repo_name, "hours": 24})

        # 3. Produce diagnosis and fix suggestions
        prompt = (
            f"You are the FuzzyLabs SRE Agent.\n"
            f"Analyze the following logs and recent commits to identify the root cause of the issue in '{service_name}' "
            f"and suggest a fix.\n\n"
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
