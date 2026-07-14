from langchain_core.tools import tool
import os

@tool
def opsmate_troubleshooting_workflow(query: str, namespace: str = "default") -> str:
    """
    Acts as an SRE Copilot using the OpsMate philosophy.
    It takes a natural language query, performs infrastructure health scans,
    and uses LLM reasoning to troubleshoot and suggest solutions.

    Args:
        query: The natural language description of the problem or intent.
        namespace: The Kubernetes namespace to focus on, if applicable.
    """
    from app.tools import scan_infrastructure, list_k8s_pods
    from app.llm import generate_diagnosis

    try:
        # 1. Gather context: infrastructure scan and pod info
        scan_results = scan_infrastructure.invoke({})
        pod_info = list_k8s_pods.invoke({"namespace": namespace})

        # 2. Formulate the prompt for the Copilot
        prompt = (
            f"You are the OpsMate AI SRE Copilot.\n"
            f"A user has provided the following query: '{query}'\n\n"
            f"Current Infrastructure Status:\n{scan_results}\n\n"
            f"Kubernetes Pod Info (Namespace: {namespace}):\n{pod_info}\n\n"
            f"Please analyze the situation and provide a detailed troubleshooting report, "
            f"including potential root causes and recommended commands to execute."
        )

        # 3. Generate diagnosis using the AI Copilot
        diagnosis = generate_diagnosis(prompt=prompt, system_instruction="You are an expert SRE log analyzer and copilot.")

        return (
            f"### 🤖 OpsMate SRE Copilot Analysis\n\n"
            f"**Query:** {query}\n\n"
            f"{diagnosis}"
        )

    except Exception as e:
        return f"Error executing OpsMate workflow: {e}"
