from langchain_core.tools import tool
from typing import List, Dict, Optional
import datetime
import uuid
import json
from app.db import init_db, SessionLocal, Incident, PostMortem, IncidentEvent, IncidentChannel
from app.llm import get_llm, get_google_sdk_client
from langchain_core.prompts import ChatPromptTemplate
from app.rag import rag_engine

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

        # Log creation event
        event = IncidentEvent(
            incident_id=inc_id,
            source="System",
            event_type="Creation",
            content=f"Incident created: {title}"
        )
        db.add(event)

        db.commit()
        return f"Incident created successfully. ID: {inc_id}"
    except Exception as e:
        db.rollback()
        return f"Error creating incident: {str(e)}"
    finally:
        db.close()

@tool
def log_incident_event(incident_id: str, event_type: str, content: str, source: str = "Agent") -> str:
    """
    Logs a significant event for an incident timeline.
    Args:
        incident_id: The ID of the incident.
        event_type: The category of event (e.g., 'Hypothesis', 'Evidence', 'Action', 'StatusChange', 'Observation').
        content: The description of what happened or what was found.
        source: Who is logging this (e.g., 'K8s_Specialist', 'Supervisor', 'Human').
    """
    db = SessionLocal()
    try:
        inc = db.query(Incident).filter(Incident.id == incident_id).first()
        if not inc:
            return f"Incident {incident_id} not found."

        event = IncidentEvent(
            incident_id=incident_id,
            source=source,
            event_type=event_type,
            content=content
        )
        db.add(event)
        db.commit()
        return f"Logged '{event_type}' event for incident {incident_id}."
    except Exception as e:
        db.rollback()
        return f"Error logging event: {str(e)}"
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

        old_status = inc.status
        inc.status = status

        # Log to legacy updates field
        if update_message:
            inc.add_update(update_message)

        # Log granular event
        event = IncidentEvent(
            incident_id=incident_id,
            source="System",
            event_type="StatusChange",
            content=f"Status changed from {old_status} to {status}. Message: {update_message}"
        )
        db.add(event)

        db.commit()
        return f"Incident {incident_id} updated to {status}."
    except Exception as e:
        db.rollback()
        return f"Error updating incident: {str(e)}"
    finally:
        db.close()

@tool
def build_incident_timeline(incident_id: str, format: str = "text") -> str:
    """
    Constructs a timeline of the incident based on logged events.
    Args:
        incident_id: The ID of the incident.
        format: 'text' (Markdown list) or 'mermaid' (Mermaid Gantt chart for visualization).
    """
    db = SessionLocal()
    try:
        inc = db.query(Incident).filter(Incident.id == incident_id).first()
        if not inc:
            return f"Incident {incident_id} not found."

        # Fetch events sorted by time
        events = db.query(IncidentEvent).filter(IncidentEvent.incident_id == incident_id).order_by(IncidentEvent.created_at).all()

        if not events:
            return "No events logged yet."

        if format.lower() == "mermaid":
            # Generate a Mermaid Gantt Chart for the timeline (IncidentFox feature)
            diagram = ["gantt", f"    title Incident Timeline: {inc.title}"]
            diagram.append("    dateFormat YYYY-MM-DD HH:mm:ss")
            diagram.append("    axisFormat %H:%M")

            diagram.append(f"    section Incident {inc.id}")

            for e in events:
                # Sanitize content for mermaid
                safe_content = e.content.replace(':', '-').replace('"', "'")[:40]
                t_str = e.created_at.strftime("%Y-%m-%d %H:%M:%S")
                # Use milestone for events
                diagram.append(f"    {e.event_type} ({e.source}) - {safe_content} :milestone, {t_str}, 0m")

            return "```mermaid\n" + "\n".join(diagram) + "\n```"

        # Default Text Format
        timeline = [f"# Incident Timeline: {inc.title} ({inc.id})"]
        timeline.append(f"**Severity:** {inc.severity} | **Status:** {inc.status}\n")

        for e in events:
            timestamp = e.created_at.strftime("%Y-%m-%d %H:%M:%S")
            icon = "ℹ️"
            if e.event_type == "Hypothesis": icon = "🤔"
            elif e.event_type == "Evidence": icon = "🔍"
            elif e.event_type == "Action": icon = "⚡"
            elif e.event_type == "StatusChange": icon = "🔄"
            elif e.event_type == "Creation": icon = "🚨"

            timeline.append(f"- **{timestamp}** {icon} [{e.source}] **{e.event_type}**: {e.content}")

        return "\n".join(timeline)
    finally:
        db.close()

@tool
def manage_incident_channels(action: str, channel_name: str, incident_id: str, platform: str = "Slack") -> str:
    """
    Manages communication channels for incidents.
    Args:
        action: 'create', 'archive', 'invite'.
        channel_name: Name of the channel (e.g., '#inc-123').
        incident_id: The ID of the incident to link.
        platform: 'Slack' or 'Zoom'.
    """
    db = SessionLocal()
    try:
        inc = db.query(Incident).filter(Incident.id == incident_id).first()
        if not inc:
             return f"Incident {incident_id} not found."

        if action == "create":
            # Check if exists
            exists = db.query(IncidentChannel).filter(
                IncidentChannel.channel_name == channel_name,
                IncidentChannel.platform == platform
            ).first()

            if exists:
                return f"Channel {channel_name} on {platform} already exists (ID: {exists.id})."

            # Create
            new_channel = IncidentChannel(
                incident_id=incident_id,
                platform=platform,
                channel_name=channel_name,
                url=f"https://{platform.lower()}.com/app/{channel_name}" # Mock URL
            )
            db.add(new_channel)

            # Log event directly since calling another tool inside a tool can be tricky depending on execution context
            # simpler to just use DB
            event = IncidentEvent(
                incident_id=incident_id,
                source="System",
                event_type="Action",
                content=f"Created {platform} channel: {channel_name}"
            )
            db.add(event)

            db.commit()
            return f"Successfully created {platform} channel '{channel_name}' for Incident {incident_id}."

        return f"Action '{action}' simulated for {channel_name}."
    except Exception as e:
        db.rollback()
        return f"Error managing channels: {e}"
    finally:
        db.close()

@tool
def list_incident_channels(incident_id: str) -> str:
    """
    Lists all communication channels linked to an incident.
    """
    db = SessionLocal()
    try:
        channels = db.query(IncidentChannel).filter(IncidentChannel.incident_id == incident_id).all()
        if not channels:
            return "No channels linked to this incident."

        return "\n".join([f"- {c.platform}: {c.channel_name} ({c.url})" for c in channels])
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
    It also uses RAG (Retrieval Augmented Generation) to fetch relevant past incidents or runbooks.
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

        # Prepare context (include new events)
        events = db.query(IncidentEvent).filter(IncidentEvent.incident_id == incident_id).order_by(IncidentEvent.created_at).all()
        events_str = "\n".join([f"[{e.created_at}] {e.event_type} ({e.source}): {e.content}" for e in events])

        # RAG Search for Context
        try:
            rag_results = rag_engine.search(f"{inc.title} {inc.description}")
            rag_context_list = []
            for doc in rag_results:
                rag_context_list.append(f"--- [Source: {doc.metadata.get('source', 'unknown')}] ---\n{doc.page_content[:300]}...")
            rag_context_str = "\n".join(rag_context_list)
        except Exception as e:
            rag_context_str = f"Warning: RAG Search failed: {str(e)}"

        context = (
            f"Title: {inc.title}\n"
            f"Severity: {inc.severity}\n"
            f"Description: {inc.description}\n"
            f"Status: {inc.status}\n"
            f"Created At: {inc.created_at}\n\n"
            f"Timeline Log:\n{events_str}\n\n"
            f"Relevant Knowledge Base Context (Past Incidents/Runbooks):\n{rag_context_str}\n"
        )

        # Best Practice 2026: Use Google GenAI SDK for large context (Incident Logs)
        client = get_google_sdk_client()
        system_msg = (
            "You are an SRE Incident Commander. "
            "Write a blameless post-mortem report in Markdown based on the following incident log.\n"
            "Use the provided Knowledge Base Context to identify patterns or suggest better remediations if applicable.\n"
            "Include:\n"
            "- Executive Summary\n"
            "- Root Cause Analysis (inference based on logs)\n"
            "- Timeline (Use the provided Timeline Log)\n"
            "- Action Items / Lessons Learned (Reference Knowledge Base if relevant)\n"
        )

        report_content = None

        # Try Gemini SDK first (better performance for large contexts)
        if client:
            try:
                response = client.models.generate_content(
                    model="gemini-1.5-flash",
                    contents=f"{system_msg}\n\nContext:\n{context}"
                )
                if response and response.text:
                    report_content = response.text
            except Exception as e:
                 print(f"Gemini SDK failed ({e}), falling back to standard LLM.")
                 report_content = None

        # Fallback to standard LLM (Ollama or LangChain adapter)
        if not report_content:
            try:
                llm = get_llm()
                prompt = ChatPromptTemplate.from_messages([
                    ("system", system_msg),
                    ("human", "{context}")
                ])

                chain = prompt | llm
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

@tool
def suggest_remediation(incident_context: str) -> str:
    """
    Suggests a remediation plan based on past incidents and available runbooks.
    Uses RAG to find similar issues and proposes steps.
    Args:
        incident_context: A description of the incident (logs, errors, title).
    """
    try:
        docs = rag_engine.search(incident_context, k=4)
        if not docs:
            return "No specific remediation found in Knowledge Base."

        summary = ["Based on Knowledge Base search:"]
        for doc in docs:
            meta = doc.metadata
            source = meta.get('source', 'unknown')
            name = meta.get('name', 'N/A')
            summary.append(f"\n[Source: {source} | Name: {name}]")
            summary.append(f"Content Snippet: {doc.page_content[:300]}...")

        return "\n".join(summary)
    except Exception as e:
        return f"Error suggestions: {str(e)}"

@tool
def generate_remediation_plan(incident_context: str) -> str:
    """
    Generates a structured, step-by-step remediation plan (Actionable Runbook) using AI.
    This is more advanced than 'suggest_remediation' as it creates a specific checklist for the current issue.

    Args:
        incident_context: Description of the incident, error logs, or symptoms.
    """
    client = get_google_sdk_client()

    prompt_text = (
        "You are a Senior Site Reliability Engineer (SRE). "
        "Based on the following incident context, generate a detailed, step-by-step remediation plan (Runbook).\n"
        "Format it as a Markdown checklist.\n"
        "Include specific commands (kubectl, gcloud, etc.) where possible.\n"
        "Assess risks for each step.\n\n"
        f"Incident Context:\n{incident_context}"
    )

    plan_content = None

    if client:
        try:
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt_text
            )
            if response and response.text:
                plan_content = f"**Generated Remediation Plan (Gemini):**\n\n{response.text}"
        except Exception as e:
            print(f"Error generating plan with Gemini SDK: {e}. Falling back to standard LLM.")
            plan_content = None

    if plan_content:
        return plan_content

    # Fallback to standard LLM (Ollama or LangChain adapter)
    llm = get_llm()
    try:
        res = llm.invoke(prompt_text)
        return f"**Generated Remediation Plan:**\n\n{res.content}"
    except Exception as e:
        return f"Error generating remediation plan: {str(e)}"
