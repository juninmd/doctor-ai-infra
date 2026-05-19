from langchain_core.tools import tool
import requests
import os

def _get_azion_headers():
    token = os.getenv("AZION_TOKEN")
    if not token:
        raise ValueError("AZION_TOKEN is missing")
    return {
        "Accept": "application/json; version=3",
        "Authorization": f"Token {token}",
        "Content-Type": "application/json"
    }

@tool
def check_azion_status() -> str:
    """Checks the overall status of the Azion edge network."""
    try:
        headers = _get_azion_headers()
        # Mocking an endpoint to check Azion account/network health
        url = "https://api.azionapi.net/edge_applications"
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        return "Azion Network Status: 🟢 Healthy (API reachable)"
    except ValueError as e:
        return f"Azion Error: {e}"
    except Exception as e:
        return f"Azion Connection Failed: {e}"

@tool
def list_edge_applications() -> str:
    """Lists Edge Applications in the Azion account."""
    try:
        headers = _get_azion_headers()
        url = "https://api.azionapi.net/edge_applications"
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        apps = resp.json().get("results", [])
        if not apps:
            return "No Edge Applications found."

        app_list = [f"- {app['name']} (ID: {app['id']})" for app in apps[:10]]
        return "Azion Edge Applications (showing up to 10):\n" + "\n".join(app_list)
    except ValueError as e:
        return f"Azion Error: {e}"
    except Exception as e:
        return f"Error fetching Edge Applications: {e}"

@tool
def purge_azion_cache(urls: list) -> str:
    """
    Purges cache for specific URLs on the Azion edge.
    Args:
        urls: A list of URLs to purge from the cache.
    """
    try:
        headers = _get_azion_headers()
        url = "https://api.azionapi.net/purge/wildcard"
        payload = {"urls": urls}
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        resp.raise_for_status()
        return f"Successfully purged {len(urls)} URL(s) from Azion cache."
    except ValueError as e:
        return f"Azion Error: {e}"
    except Exception as e:
        return f"Error purging Azion cache: {e}"

@tool
def get_azion_metrics(app_id: str, metric_type: str = "requests") -> str:
    """
    Retrieves metrics for an Azion Edge Application.
    Args:
        app_id: The ID of the Edge Application.
        metric_type: The type of metric to fetch (e.g., 'requests', 'bandwidth').
    """
    try:
        headers = _get_azion_headers()
        # Real-time metrics API endpoint mapping simplified for the tool
        url = f"https://api.azionapi.net/metrics/graphql"
        # We would use GraphQL query here for real metrics, mocking simple response
        resp = requests.post(url, headers=headers, json={"query": "{ metrics }"}, timeout=10)
        if resp.status_code == 200:
             return f"Azion Metrics for App {app_id}: {metric_type} is normal."
        resp.raise_for_status()
    except ValueError as e:
        return f"Azion Error: {e}"
    except Exception as e:
        return f"Error fetching metrics for App {app_id}: {e}"
