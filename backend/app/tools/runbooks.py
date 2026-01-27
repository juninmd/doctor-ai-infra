from langchain_core.tools import tool
from typing import List, Dict

# Mock Service Catalog with Topology Info
SERVICE_CATALOG = {
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
        allowed = SERVICE_CATALOG[target_service].get("runbooks", [])
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

@tool
def get_service_dependencies(service_name: str) -> str:
    """
    Returns the list of downstream dependencies (services/DBs called by this service).
    Use this to understand what might be breaking the service.
    """
    service = SERVICE_CATALOG.get(service_name)
    if not service:
        return f"Service '{service_name}' not found."

    deps = service.get("dependencies", [])
    if not deps:
        return f"Service '{service_name}' has no registered dependencies."

    return f"Dependencies for {service_name}: {', '.join(deps)}"

@tool
def get_service_topology(service_name: str) -> str:
    """
    Returns the full immediate topology (upstream callers and downstream dependencies).
    Use this to identify impact (who calls me?) and root cause (who do I call?).
    """
    if service_name not in SERVICE_CATALOG:
        return f"Service '{service_name}' not found."

    downstream = SERVICE_CATALOG[service_name].get("dependencies", [])

    # Find upstream (who calls this service?)
    upstream = []
    for name, details in SERVICE_CATALOG.items():
        if service_name in details.get("dependencies", []):
            upstream.append(name)

    return (
        f"Topology for {service_name}:\n"
        f"  [Upstream/Callers]: {', '.join(upstream) if upstream else 'None'}\n"
        f"  ↓\n"
        f"  [{service_name}]\n"
        f"  ↓\n"
        f"  [Downstream/Dependencies]: {', '.join(downstream) if downstream else 'None'}"
    )
