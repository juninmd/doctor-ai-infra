from langchain_core.tools import tool
import os
import requests

@tool
def check_azion_edge() -> str:
    """Checks the status of Azion Edge Applications."""
    token = os.getenv("AZION_TOKEN")
    if not token:
        return "Error: AZION_TOKEN is missing. Cannot check Azion Edge."

    headers = {"Authorization": f"Token {token}", "Accept": "application/json; version=3"}
    try:
        resp = requests.get("https://api.azionapi.net/edge_applications", headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        apps = data.get("results", [])
        if not apps:
            return "No Azion Edge Applications found."

        result = [f"Found {len(apps)} Azion Edge Applications:"]
        for app in apps[:5]:
            result.append(f"- {app.get('name')} (ID: {app.get('id')}) - Active: {app.get('active')}")
        return "\n".join(result)
    except Exception as e:
        return f"Error checking Azion Edge Applications: {str(e)}"

@tool
def check_azion_waf() -> str:
    """Checks the status of Azion WAF (Web Application Firewall)."""
    token = os.getenv("AZION_TOKEN")
    if not token:
        return "Error: AZION_TOKEN is missing. Cannot check Azion WAF."

    headers = {"Authorization": f"Token {token}", "Accept": "application/json; version=3"}
    try:
        resp = requests.get("https://api.azionapi.net/edge_firewall", headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        firewalls = data.get("results", [])
        if not firewalls:
            return "No Azion WAF Configurations found."

        result = [f"Found {len(firewalls)} Azion WAF Configurations:"]
        for fw in firewalls[:5]:
            result.append(f"- {fw.get('name')} (ID: {fw.get('id')}) - Active: {fw.get('is_active')}")
        return "\n".join(result)
    except Exception as e:
        return f"Error checking Azion WAF: {str(e)}"

@tool
def purge_azion_cache(urls: str) -> str:
    """
    Purges URLs from Azion Edge Cache.
    Args:
        urls: Comma-separated list of URLs to purge.
    """
    token = os.getenv("AZION_TOKEN")
    if not token:
        return "Error: AZION_TOKEN is missing. Cannot purge Azion Cache."

    headers = {"Authorization": f"Token {token}", "Accept": "application/json; version=3", "Content-Type": "application/json"}

    url_list = [url.strip() for url in urls.split(",")]

    payload = {
        "urls": url_list,
        "method": "delete"
    }

    try:
        resp = requests.post("https://api.azionapi.net/purge/url", headers=headers, json=payload, timeout=10)
        resp.raise_for_status()
        return f"Successfully requested cache purge for URLs: {urls}"
    except Exception as e:
        return f"Error purging Azion Cache: {str(e)}"
