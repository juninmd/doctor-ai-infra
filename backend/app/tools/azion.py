from langchain_core.tools import tool
import os
import requests


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
    """Checks the status of the Azion Edge CDN infrastructure."""
    try:
        headers = _get_azion_headers()
        resp = requests.get("https://api.azionapi.net/edge_applications", headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        count = data.get("count", 0)
        return f"Azion Edge CDN is Active. {count} edge applications found."
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
def purge_azion_cache(urls: str) -> str:
    """
    Purges cache for specific URLs in Azion Edge CDN.
    Args:
        urls: Comma-separated list of URLs to purge.
    """
    try:
        headers = _get_azion_headers()
        url_list = [u.strip() for u in urls.split(",") if u.strip()]
        if not url_list:
            return "No URLs provided for cache purge."
        payload = {"urls": url_list, "method": "delete"}
        resp = requests.post("https://api.azionapi.net/purge/url", headers=headers, json=payload, timeout=10)
        resp.raise_for_status()
        return f"Successfully purged cache for {len(url_list)} URL(s) in Azion."
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
        url = "https://api.azionapi.net/metrics/graphql"
        resp = requests.post(url, headers=headers, json={"query": "{ metrics }"}, timeout=10)
        if resp.status_code == 200:
            return f"Azion Metrics for App {app_id}: {metric_type} is normal."
        resp.raise_for_status()
    except ValueError as e:
        return f"Azion Error: {e}"
    except Exception as e:
        return f"Error fetching metrics for App {app_id}: {e}"