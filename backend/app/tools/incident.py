from langchain_core.tools import tool
from typing import List, Dict, Optional
import datetime
import uuid
import json
from app.db import init_db, SessionLocal, Incident, PostMortem
from app.llm import get_llm
from langchain_core.prompts import ChatPromptTemplate

# Ensure DB is initialized
init_db()

@tool
def create_incident(title: str, severity: str, description: str) -> str:
    """
    Creates a new incident.
    Args:
        title: Short summary of the incident.
        severity: Severity level (SEV-1, SEV-2, SEV-3).
        description: Detailed description of the issue.
    """
    db = SessionLocal()
    try:
        inc_id = str(uuid.uuid4())[:8]
        new_inc = Incident(
            id=inc_id,
            title=title,
            severity=severity,
            description=description,
            status="OPEN"
        )
        db.add(new_inc)
        db.commit()
        return f"Incident created successfully. ID: {inc_id}"
    except Exception as e:
        db.rollback()
        return f"Error creating incident: {str(e)}"
    finally:
        db.close()

@tool
def update_incident_status(incident_id: str, status: str, update_message: str = "") -> str:
    """
    Updates the status of an existing incident.
    Args:
        incident_id: The ID of the incident.
        status: New status (e.g., INVESTIGATING, IDENTIFIED, RESOLVED, CLOSED).
        update_message: Optional log message explaining the update.
    """
    db = SessionLocal()
    try:
        inc = db.query(Incident).filter(Incident.id == incident_id).first()
        if not inc:
            return f"Incident {incident_id} not found."

        inc.status = status
        if update_message:
            inc.add_update(update_message)

        db.commit()
        return f"Incident {incident_id} updated to {status}."
    except Exception as e:
        db.rollback()
        return f"Error updating incident: {str(e)}"
    finally:
        db.close()

@tool
def list_incidents(status: Optional[str] = None) -> str:
    """
    Lists incidents, optionally filtered by status.
    Args:
        status: Filter by status (e.g., OPEN, RESOLVED).
    """
    db = SessionLocal()
    try:
        query = db.query(Incident)
        if status:
            query = query.filter(Incident.status == status)

        incidents = query.all()
        results = []
        for inc in incidents:
            results.append(f"[{inc.id}] {inc.title} ({inc.severity}) - {inc.status}")

        if not results:
            return "No incidents found."
        return "\n".join(results)
    finally:
        db.close()

@tool
def get_incident_details(incident_id: str) -> str:
    """
    Retrieves full details of an incident, including history.
    Args:
        incident_id: The ID of the incident.
    """
    db = SessionLocal()
    try:
        inc = db.query(Incident).filter(Incident.id == incident_id).first()
        if not inc:
            return f"Incident {incident_id} not found."

        details = inc.to_dict()
        return json.dumps(details, indent=2)
    finally:
        db.close()

@tool
def generate_postmortem(incident_id: str) -> str:
    """
    Generates a Post-Mortem report for a resolved incident using AI.
    It reads the incident history and updates, then writes a Markdown report.
    Args:
        incident_id: The ID of the resolved incident.
    """
    db = SessionLocal()
    try:
        inc = db.query(Incident).filter(Incident.id == incident_id).first()
        if not inc:
            return f"Incident {incident_id} not found."

        # Check if exists
        if inc.post_mortem:
            return f"Post-Mortem already exists for {incident_id}. (ID: {inc.post_mortem.id})"

        # Prepare context
        updates_str = inc.updates
        context = (
            f"Title: {inc.title}\n"
            f"Severity: {inc.severity}\n"
            f"Description: {inc.description}\n"
            f"Status: {inc.status}\n"
            f"Created At: {inc.created_at}\n"
            f"Updates: {updates_str}\n"
        )

        llm = get_llm()
        prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "You are an SRE Incident Commander. "
                "Write a blameless post-mortem report in Markdown based on the following incident log.\n"
                "Include:\n"
                "- Executive Summary\n"
                "- Root Cause Analysis (inference based on logs)\n"
                "- Timeline\n"
                "- Action Items\n"
            )),
            ("human", "{context}")
        ])

        chain = prompt | llm
        try:
            res = chain.invoke({"context": context})
            report_content = res.content
        except Exception as llm_error:
            return f"Error calling LLM for post-mortem: {str(llm_error)}"

        # Save to DB
        pm = PostMortem(incident_id=incident_id, content=report_content)
        db.add(pm)
        db.commit()

        return f"Post-Mortem generated and saved for {incident_id}.\n\nPreview:\n{report_content[:500]}..."
    except Exception as e:
        db.rollback()
        return f"Error generating post-mortem: {str(e)}"
    finally:
        db.close()
