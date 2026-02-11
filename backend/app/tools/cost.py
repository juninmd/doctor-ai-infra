from langchain_core.tools import tool
from app.llm import get_google_sdk_client, get_llm
import concurrent.futures
import os
import importlib

@tool
def estimate_gcp_cost() -> str:
    """
    Estimates the monthly GCP bill based on currently active resources.
    Scans Compute Engine and Cloud SQL instances, then uses AI to estimate costs.
    Note: This is an estimation based on public pricing knowledge, not the actual Billing API.
    """
    use_real = os.getenv("USE_REAL_TOOLS", "true").lower() == "true"

    list_compute_instances = None
    get_gcp_sql_instances = None

    # Try importing real tools first if requested
    if use_real:
        try:
            # Dynamic import to avoid circular dependency issues at module level
            real_module = importlib.import_module("app.tools.real")
            list_compute_instances = getattr(real_module, "list_compute_instances", None)
            get_gcp_sql_instances = getattr(real_module, "get_gcp_sql_instances", None)
        except ImportError:
            print("Warning: Could not import app.tools.real")
            pass

    # Fallback to mocks if real tools are missing or not requested
    if not list_compute_instances or not get_gcp_sql_instances:
        try:
            mock_module = importlib.import_module("app.tools.mocks")
            list_compute_instances = getattr(mock_module, "list_compute_instances", None)
            get_gcp_sql_instances = getattr(mock_module, "get_gcp_sql_instances", None)
        except ImportError:
            return "Error: Could not import GCP tools from mocks either."

    if not list_compute_instances or not get_gcp_sql_instances:
        return "Error: Tools 'list_compute_instances' or 'get_gcp_sql_instances' not found."

    resources = []

    # 1. Gather Resource Data
    # Note: Using ThreadPool for parallel execution
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Pass empty dict as input for tools taking optional args
        future_vm = executor.submit(list_compute_instances.invoke, {})
        future_sql = executor.submit(get_gcp_sql_instances.invoke, {})

        try:
            # Result might be a string (error) or list string
            vm_res = future_vm.result()
            resources.append(f"Compute Engine Instances:\n{vm_res}")
        except Exception as e:
            resources.append(f"Compute Engine: Error ({str(e)})")

        try:
            sql_res = future_sql.result()
            resources.append(f"Cloud SQL Instances:\n{sql_res}")
        except Exception as e:
            resources.append(f"Cloud SQL: Error ({str(e)})")

    resource_summary = "\n\n".join(resources)

    # 2. AI Estimation
    prompt = (
        "You are an expert GCP FinOps & Cost Analyst.\n"
        "Based on the following list of active GCP resources, estimate the monthly cost.\n"
        "Assume standard pricing (us-central1), 730 hours/month usage unless status says otherwise.\n"
        "Provide a breakdown by service and a total estimated monthly bill.\n"
        "Be conservative but realistic.\n\n"
        f"RESOURCES:\n{resource_summary}\n\n"
        "OUTPUT FORMAT:\n"
        "- **Compute Engine**: $X.XX (Breakdown...)\n"
        "- **Cloud SQL**: $X.XX (Breakdown...)\n"
        "- **Total Estimated Monthly Cost**: $X.XX\n"
        "\n(Disclaimer: AI-generated estimate. Check GCP Billing Console for actuals.)"
    )

    # Strategy 1: Google GenAI SDK (Gemini 1.5 Flash)
    client = get_google_sdk_client()
    if client:
        try:
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt
            )
            return response.text
        except Exception as e:
            print(f"Gemini SDK failed: {e}. Falling back to standard LLM.")

    # Strategy 2: Standard LLM Fallback
    try:
        llm = get_llm()
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        return f"Error generating cost estimate: {str(e)}"
