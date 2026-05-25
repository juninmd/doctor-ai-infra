from langchain_core.tools import tool
import os
import requests

@tool
def check_azion_status() -> str:
    """
    Checks the status of the Azion Edge CDN infrastructure.
    Authenticates via the AZION_TOKEN environment variable.
    """
    token = os.getenv("AZION_TOKEN")
    if not token:
        return "Error: AZION_TOKEN missing. Cannot check Azion status."

    headers = {"Authorization": f"Token {token}", "Accept": "application/json"}
    try:
        # Example endpoint for fetching edge applications
        resp = requests.get("https://api.azionapi.net/edge_applications", headers=headers, timeout=10)
        resp.raise_for_status()

        data = resp.json()
        count = data.get("count", 0)
        return f"Azion Edge CDN is Active. {count} edge applications found."
    except Exception as e:
        return f"Azion Error: {str(e)}"

@tool
def purge_azion_cache(urls: str) -> str:
    """
    Purges cache for specific URLs in Azion Edge CDN.
    Args:
        urls: Comma-separated list of URLs to purge.
    """
    token = os.getenv("AZION_TOKEN")
    if not token:
        return "Error: AZION_TOKEN missing. Cannot purge Azion cache."

    headers = {
        "Authorization": f"Token {token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    url_list = [u.strip() for u in urls.split(",") if u.strip()]
    if not url_list:
        return "No URLs provided for cache purge."

    payload = {
        "urls": url_list,
        "method": "delete"
    }

    try:
        resp = requests.post("https://api.azionapi.net/purge/url", json=payload, headers=headers, timeout=10)
        resp.raise_for_status()
        return f"Successfully purged cache for {len(url_list)} URL(s) in Azion."
    except Exception as e:
        return f"Azion Purge Error: {str(e)}"
