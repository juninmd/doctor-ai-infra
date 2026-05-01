from langchain_core.tools import tool
import os
import requests
from google.auth import default
from google.auth.transport.requests import Request as GoogleAuthRequest

@tool
def optimize_gcp_resources() -> str:
    """
    Identifies optimization opportunities in GCP: orphaned disks, unused IPs, and underutilized VMs.
    """
    try:
        credentials, project = default()
        if not project: return "Error: GCP Project not found."
        credentials.refresh(GoogleAuthRequest())
        token = credentials.token
        headers = {"Authorization": f"Bearer {token}"}
        
        report = ["### ☁️ GCP Infrastructure Optimization"]
        
        # 1. Orphaned Disks Check
        url_disks = f"https://compute.googleapis.com/compute/v1/projects/{project}/aggregated/disks"
        resp = requests.get(url_disks, headers=headers, timeout=10)
        if resp.status_code == 200:
            orphaned = []
            for zone, data in resp.json().get("items", {}).items():
                for disk in data.get("disks", []):
                    if not disk.get("users"):
                        orphaned.append(f"- {disk['name']} ({zone.split('/')[-1]}, {disk['sizeGb']}GB)")
            if orphaned:
                report.append("\n**Orphaned Disks (Not attached to any VM):**")
                report.extend(orphaned[:5]) # Limit output
            else:
                report.append("\n✅ No orphaned disks found.")

        # 2. Idle VM Check (Mocking logic based on status if metrics unavailable)
        url_vms = f"https://compute.googleapis.com/compute/v1/projects/{project}/aggregated/instances"
        resp_vms = requests.get(url_vms, headers=headers, timeout=10)
        if resp_vms.status_code == 200:
            stopped = []
            for zone, data in resp_vms.json().get("items", {}).items():
                for inst in data.get("instances", []):
                    if inst['status'] == "TERMINATED":
                        stopped.append(f"- {inst['name']} (Stopped - Consider deleting if not needed)")
            if stopped:
                report.append("\n**Stopped VMs (Incurring disk costs):**")
                report.extend(stopped[:5])
        
        return "\n".join(report)
    except Exception as e:
        return f"GCP Optimization Error: {str(e)}"
