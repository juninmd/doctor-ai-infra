from langchain_core.tools import tool
from typing import List, Dict

# Mock Service Catalog
SERVICE_CATALOG = {
    "payment-api": {
        "owner": "Team Checkout",
        "description": "Handles payment processing.",
        "runbooks": ["restart_service", "scale_up", "rollback_deploy"],
        "tier": "Tier-1"
    },
    "auth-service": {
        "owner": "Team Identity",
        "description": "Handles user authentication.",
        "runbooks": ["restart_service", "flush_cache"],
        "tier": "Tier-0"
    },
    "frontend-web": {
        "owner": "Team Frontend",
        "description": "Next.js public facing site.",
        "runbooks": ["clear_cdn_cache", "rollback_deploy"],
        "tier": "Tier-2"
    }
}

# Mock Runbook Library
RUNBOOKS = {
    "restart_service": "Restarts the Kubernetes deployment for the service. Safe to run during outages.",
    "scale_up": "Increases replica count by 2. Use when CPU is > 80%.",
    "rollback_deploy": "Reverts to the previous stable docker image tag.",
    "flush_cache": "Clears Redis cache keys for the service.",
    "clear_cdn_cache": "Purges Azion/Cloudflare Edge cache."
}

@tool
def list_runbooks() -> str:
    """Lists all available automated runbooks and their descriptions."""
    results = [f"- {name}: {desc}" for name, desc in RUNBOOKS.items()]
    return "\n".join(results)

@tool
def execute_runbook(runbook_name: str, target_service: str) -> str:
    """
    Executes a specific runbook against a target service.
    Args:
        runbook_name: The name of the runbook to run.
        target_service: The service to target (e.g., payment-api).
    """
    if runbook_name not in RUNBOOKS:
        return f"Error: Runbook '{runbook_name}' does not exist. Use list_runbooks() to see available options."

    # Validation against catalog
    if target_service in SERVICE_CATALOG:
        allowed = SERVICE_CATALOG[target_service]["runbooks"]
        if runbook_name not in allowed:
            return f"Warning: Runbook '{runbook_name}' is not explicitly listed for '{target_service}', but executing anyway via Admin override..."

    # Mock execution logic
    return f"SUCCESS: Executed runbook '{runbook_name}' on '{target_service}'. Operation completed in 2.4s."

@tool
def lookup_service(service_name: str) -> str:
    """
    Retrieves metadata about a service from the Service Catalog.
    Args:
        service_name: The name of the service to look up.
    """
    service = SERVICE_CATALOG.get(service_name)
    if not service:
        # Fuzzy match
        for name, details in SERVICE_CATALOG.items():
            if service_name in name:
                return f"Did you mean '{name}'? \n{details}"
        return f"Service '{service_name}' not found in catalog."

    return f"Service: {service_name}\nDetails: {service}"
