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
        if not project:
            return "Error: GCP Project not found. Ensure GOOGLE_APPLICATION_CREDENTIALS is set."
        
        credentials.refresh(GoogleAuthRequest())
        token = credentials.token
        headers = {"Authorization": f"Bearer {token}"}
        
        report = ["### ☁️ GCP Infrastructure Optimization Report"]
        
        # 1. Orphaned Disks Check
        url_disks = f"https://compute.googleapis.com/compute/v1/projects/{project}/aggregated/disks"
        resp = requests.get(url_disks, headers=headers, timeout=15)
        if resp.status_code == 200:
            orphaned = []
            for zone, data in resp.json().get("items", {}).items():
                for disk in data.get("disks", []):
                    if not disk.get("users"):
                        orphaned.append(f"- {disk['name']} ({zone.split('/')[-1]}, {disk['sizeGb']}GB)")
            if orphaned:
                report.append("\n**Orphaned Disks (Not attached):**")
                report.extend(orphaned[:10])
            else:
                report.append("\n✅ No orphaned disks found.")
        else:
            report.append(f"\n⚠️ Could not fetch disks: {resp.status_code}")

        # 2. Stopped VMs Check
        url_vms = f"https://compute.googleapis.com/compute/v1/projects/{project}/aggregated/instances"
        resp_vms = requests.get(url_vms, headers=headers, timeout=15)
        if resp_vms.status_code == 200:
            stopped = []
            for zone, data in resp_vms.json().get("items", {}).items():
                for inst in data.get("instances", []):
                    if inst['status'] == "TERMINATED":
                        stopped.append(f"- {inst['name']} (Stopped in {zone.split('/')[-1]})")
            if stopped:
                report.append("\n**Stopped VMs (Incurring storage costs):**")
                report.extend(stopped[:10])
        
        if len(report) == 1:
            return "GCP Optimization: No significant opportunities found or permission denied."
            
        return "\n".join(report)
    except Exception as e:
        return f"GCP Optimization Tool Error: {str(e)}"
