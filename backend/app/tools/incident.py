from langchain_core.tools import tool
from typing import List, Dict, Optional
import uuid
import datetime

# Global in-memory storage for incidents
INCIDENTS = []

@tool
def create_incident(title: str, severity: str, description: str) -> str:
    """
    Creates a new incident.
    Args:
        title: Short summary of the incident.
        severity: Severity level (SEV-1, SEV-2, SEV-3).
        description: Detailed description of the issue.
    """
    incident_id = str(uuid.uuid4())[:8]
    incident = {
        "id": incident_id,
        "title": title,
        "severity": severity,
        "description": description,
        "status": "OPEN",
        "created_at": datetime.datetime.now().isoformat(),
        "updates": []
    }
    INCIDENTS.append(incident)
    return f"Incident created successfully. ID: {incident_id}"

@tool
def update_incident_status(incident_id: str, status: str, update_message: str = "") -> str:
    """
    Updates the status of an existing incident.
    Args:
        incident_id: The ID of the incident.
        status: New status (e.g., INVESTIGATING, IDENTIFIED, RESOLVED, CLOSED).
        update_message: Optional log message explaining the update.
    """
    for inc in INCIDENTS:
        if inc["id"] == incident_id:
            inc["status"] = status
            if update_message:
                inc["updates"].append(f"{datetime.datetime.now().isoformat()}: {update_message}")
            return f"Incident {incident_id} updated to {status}."
    return f"Incident {incident_id} not found."

@tool
def list_incidents(status: Optional[str] = None) -> str:
    """
    Lists incidents, optionally filtered by status.
    Args:
        status: Filter by status (e.g., OPEN, RESOLVED).
    """
    results = []
    for inc in INCIDENTS:
        if status and inc["status"] != status:
            continue
        results.append(f"[{inc['id']}] {inc['title']} ({inc['severity']}) - {inc['status']}")

    if not results:
        return "No incidents found."
    return "\n".join(results)

@tool
def get_incident_details(incident_id: str) -> str:
    """
    Retrieves full details of an incident, including history.
    Args:
        incident_id: The ID of the incident.
    """
    for inc in INCIDENTS:
        if inc["id"] == incident_id:
            return str(inc)
    return f"Incident {incident_id} not found."
