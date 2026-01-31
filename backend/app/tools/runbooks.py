from langchain_core.tools import tool
from typing import List, Dict
import json
from sqlalchemy.orm import Session
from app.db import SessionLocal, Service, Runbook

# --- Mock Data for Bootstrap ---
INITIAL_SERVICE_CATALOG = {
    "payment-api": {
        "owner": "Team Checkout",
        "description": "Handles payment processing.",
        "runbooks": ["restart_service", "scale_up", "rollback_deploy"],
        "tier": "Tier-1",
        "dependencies": ["auth-service", "fraud-detection", "payment-db"],
        "telemetry": "https://app.datadoghq.com/dashboard/payment-api"
    },
    "auth-service": {
        "owner": "Team Identity",
        "description": "Handles user authentication (OAuth2/JWT).",
        "runbooks": ["restart_service", "flush_cache"],
        "tier": "Tier-0",
        "dependencies": ["users-db", "redis-cache"],
        "telemetry": "https://app.datadoghq.com/dashboard/auth-service"
    },
    "frontend-web": {
        "owner": "Team Frontend",
        "description": "Next.js public facing site.",
        "runbooks": ["clear_cdn_cache", "rollback_deploy"],
        "tier": "Tier-2",
        "dependencies": ["payment-api", "product-api"],
        "telemetry": "https://app.datadoghq.com/dashboard/frontend"
    },
    "fraud-detection": {
        "owner": "Team Security",
        "description": "Analyzes transactions for fraud patterns.",
        "runbooks": ["restart_service"],
        "tier": "Tier-2",
        "dependencies": ["analysis-db"],
        "telemetry": "https://app.datadoghq.com/dashboard/fraud"
    },
    "product-api": {
        "owner": "Team Catalog",
        "description": "Serves product details.",
        "runbooks": ["restart_service"],
        "tier": "Tier-1",
        "dependencies": ["product-db"],
        "telemetry": "https://app.datadoghq.com/dashboard/product-api"
    }
}

INITIAL_RUNBOOKS = {
    "restart_service": "Restarts the Kubernetes deployment for the service. Safe to run during outages.",
    "scale_up": "Increases replica count by 2. Use when CPU is > 80%.",
    "rollback_deploy": "Reverts to the previous stable docker image tag.",
    "flush_cache": "Clears Redis cache keys for the service.",
    "clear_cdn_cache": "Purges Azion/Cloudflare Edge cache."
}

def bootstrap_catalog():
    """Populates the database with initial services and runbooks if empty."""
    db = SessionLocal()
    try:
        if db.query(Service).first():
            return # Already populated

        print("Bootstrapping Service Catalog and Runbooks...")

        # 1. Create Runbooks
        r_objects = {}
        for name, desc in INITIAL_RUNBOOKS.items():
            r = Runbook(name=name, description=desc, implementation_key=name)
            db.add(r)
            r_objects[name] = r

        db.commit()

        # 2. Create Services (First pass: ensure all exist)
        # Collect all unique service names including dependencies
        all_services = set(INITIAL_SERVICE_CATALOG.keys())
        for details in INITIAL_SERVICE_CATALOG.values():
            all_services.update(details.get("dependencies", []))

        s_objects = {}
        for s_name in all_services:
            if s_name in INITIAL_SERVICE_CATALOG:
                d = INITIAL_SERVICE_CATALOG[s_name]
                s = Service(
                    name=s_name,
                    owner=d["owner"],
                    description=d["description"],
                    tier=d["tier"],
                    telemetry_url=d.get("telemetry")
                )
            else:
                # Inferred external service (DBs, etc)
                s = Service(
                    name=s_name,
                    owner="Unknown",
                    description="Inferred dependency",
                    tier="External",
                    telemetry_url=None
                )
            db.add(s)
            s_objects[s_name] = s

        db.commit()

        # 3. Link Dependencies and Runbooks
        for s_name, details in INITIAL_SERVICE_CATALOG.items():
            service = s_objects[s_name]

            # Link Runbooks
            for r_name in details.get("runbooks", []):
                if r_name in r_objects:
                    service.runbooks.append(r_objects[r_name])

            # Link Dependencies
            for dep_name in details.get("dependencies", []):
                if dep_name in s_objects:
                    service.dependencies.append(s_objects[dep_name])

        db.commit()
        print("Bootstrap complete.")

    except Exception as e:
        db.rollback()
        print(f"Error bootstrapping catalog: {e}")
    finally:
        db.close()


@tool
def list_runbooks() -> str:
    """Lists all available automated runbooks and their descriptions."""
    db = SessionLocal()
    try:
        runbooks = db.query(Runbook).all()
        results = [f"- {r.name}: {r.description}" for r in runbooks]
        return "\n".join(results)
    finally:
        db.close()

@tool
def execute_runbook(runbook_name: str, target_service: str) -> str:
    """
    Executes a specific runbook against a target service.
    Args:
        runbook_name: The name of the runbook to run.
        target_service: The service to target (e.g., payment-api).
    """
    db = SessionLocal()
    try:
        service = db.query(Service).filter(Service.name == target_service).first()
        if not service:
             # Check if it's an external service?
             return f"Error: Service '{target_service}' not found in catalog."

        runbook = db.query(Runbook).filter(Runbook.name == runbook_name).first()
        if not runbook:
            return f"Error: Runbook '{runbook_name}' does not exist."

        # Verify association
        allowed_runbooks = [r.name for r in service.runbooks]
        if runbook_name not in allowed_runbooks:
             return f"Warning: Runbook '{runbook_name}' is not linked to '{target_service}'. Executing anyway via override..."

        # Mock execution logic (The implementation would go here, dispatching by runbook.implementation_key)
        return f"SUCCESS: Executed runbook '{runbook_name}' on '{target_service}'. Operation completed."
    finally:
        db.close()

@tool
def lookup_service(service_name: str) -> str:
    """
    Retrieves metadata about a service from the Service Catalog.
    Args:
        service_name: The name of the service to look up.
    """
    db = SessionLocal()
    try:
        service = db.query(Service).filter(Service.name == service_name).first()
        if not service:
            # Fuzzy search
            partial = db.query(Service).filter(Service.name.contains(service_name)).first()
            if partial:
                return f"Did you mean '{partial.name}'? \n{json.dumps(partial.to_dict(), indent=2)}"
            return f"Service '{service_name}' not found."

        return f"Service: {service.name}\nDetails: {json.dumps(service.to_dict(), indent=2)}"
    finally:
        db.close()

@tool
def get_service_dependencies(service_name: str) -> str:
    """
    Returns the list of downstream dependencies (services/DBs called by this service).
    """
    db = SessionLocal()
    try:
        service = db.query(Service).filter(Service.name == service_name).first()
        if not service:
            return f"Service '{service_name}' not found."

        deps = [d.name for d in service.dependencies]
        if not deps:
            return f"Service '{service_name}' has no registered dependencies."

        return f"Dependencies for {service_name}: {', '.join(deps)}"
    finally:
        db.close()

@tool
def get_service_topology(service_name: str) -> str:
    """
    Returns the full immediate topology (upstream callers and downstream dependencies).
    """
    db = SessionLocal()
    try:
        service = db.query(Service).filter(Service.name == service_name).first()
        if not service:
            return f"Service '{service_name}' not found."

        downstream = [d.name for d in service.dependencies]
        upstream = [u.name for u in service.callers] # Relies on backref="callers"

        return (
            f"Topology for {service_name}:\n"
            f"  [Upstream/Callers]: {', '.join(upstream) if upstream else 'None'}\n"
            f"  ↓\n"
            f"  [{service_name}]\n"
            f"  ↓\n"
            f"  [Downstream/Dependencies]: {', '.join(downstream) if downstream else 'None'}"
        )
    finally:
        db.close()
