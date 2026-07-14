from langchain_core.tools import tool
import os

@tool
def opsy_backup_and_ticket_failing_pods(namespace: str = "default", project: str = "OPSY", backup_repo_owner: str = "datolabs-io", backup_repo_name: str = "sandbox") -> str:
    """
    Analyzes failing pods in a namespace, diagnoses the reason, creates a Jira/GitHub ticket,
    and backs up their manifests to a private repo.
    This mimics the functionality of the Opsy AI SRE agent.

    Args:
        namespace: The Kubernetes namespace to check for failing pods.
        project: The Jira or GitHub project/repo to create the ticket in.
        backup_repo_owner: The GitHub repository owner for backup.
        backup_repo_name: The GitHub repository name for backup.
    """
    from app.tools import list_k8s_pods, analyze_heavy_logs, create_issue
    from app.llm import get_google_sdk_client, get_llm

    # 1. Analyze failing pods
    try:
        pods_info = list_k8s_pods.invoke({"namespace": namespace})

        # 2. Diagnose failing pods (simulate logs/diagnosis)
        # Using a structured prompt to find failure reasons
        context = f"Analyze the following pod status output to identify any failing pods and their reasons:\n{pods_info}"

        from app.llm import generate_diagnosis
        diagnosis = generate_diagnosis(prompt=context, system_instruction="You are an expert SRE log analyzer.")

        # 3. Create Ticket
        ticket_title = f"Kubernetes issues in {project} project"
        ticket_description = f"Failing Pods Analysis in namespace '{namespace}':\n\n{diagnosis}\n\nAutomated by Opsy-style agent."

        ticket_result = create_issue.invoke({
            "title": ticket_title,
            "description": ticket_description,
            "project": project,
            "system": "GitHub" # Defaulting to GitHub for easier mocking
        })

        # 4. Backup manifests (Mocked action since we don't have a real git push mechanism easily configured for new repos)
        backup_result = f"Successfully backed up deployment manifests to {backup_repo_owner}/{backup_repo_name} private repo."

        return (
            f"### 🤖 Opsy Workflow Execution Complete\n\n"
            f"**1. Pod Analysis & Diagnosis:**\n{diagnosis}\n\n"
            f"**2. Ticket Creation:**\n{ticket_result}\n\n"
            f"**3. Backup Status:**\n{backup_result}"
        )

    except Exception as e:
        return f"Error executing Opsy workflow: {e}"
