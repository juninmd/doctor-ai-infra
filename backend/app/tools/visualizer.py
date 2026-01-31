from langchain_core.tools import tool
from app.db import SessionLocal, Service

@tool
def generate_topology_diagram(focus_service: str = "all") -> str:
    """
    Generates a Mermaid.js diagram code block representing the service topology.
    Use this when the user asks for a visual representation of the architecture or dependencies.

    Args:
        focus_service: The name of the service to focus on, or "all" for the full map.
    """

    mermaid_code = ["graph TD"]

    # Styles for nodes
    mermaid_code.append("    classDef db fill:#e1f5fe,stroke:#01579b,stroke-width:2px,color:#000;")
    mermaid_code.append("    classDef service fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#000;")
    mermaid_code.append("    classDef tier1 fill:#fff9c4,stroke:#fbc02d,stroke-width:2px,color:#000;")
    mermaid_code.append("    classDef unknown fill:#f5f5f5,stroke:#9e9e9e,stroke-width:1px,stroke-dasharray: 5 5,color:#666;")

    db = SessionLocal()
    try:
        # Reconstruct Catalog from DB for visualization logic
        services_obj = db.query(Service).all()
        service_catalog = {s.name: s.to_dict() for s in services_obj}

        if focus_service != "all" and focus_service in service_catalog:
            # Focus mode: Show upstream -> Service -> Downstream
            target = service_catalog[focus_service]

            # Add target
            mermaid_code.append(f"    {focus_service}([{focus_service}])")

            # Dependencies
            for dep in target.get("dependencies", []):
                mermaid_code.append(f"    {focus_service} --> {dep}([{dep}])")
                # Style dependency
                if "db" in dep:
                    mermaid_code.append(f"    class {dep} db;")
                elif dep in service_catalog:
                    mermaid_code.append(f"    class {dep} service;")
                else:
                    mermaid_code.append(f"    class {dep} unknown;")

            # Find upstream
            for name, details in service_catalog.items():
                if focus_service in details.get("dependencies", []):
                    mermaid_code.append(f"    {name}([{name}]) --> {focus_service}")
                    if "db" in name:
                        mermaid_code.append(f"    class {name} db;")
                    else:
                        mermaid_code.append(f"    class {name} service;")

            # Style target
            mermaid_code.append(f"    class {focus_service} tier1;")

        else:
            # Full map
            for name, details in service_catalog.items():
                mermaid_code.append(f"    {name}([{name}])")

                # Dependencies
                for dep in details.get("dependencies", []):
                    mermaid_code.append(f"    {name} --> {dep}([{dep}])")

                    # Style unknown dependencies
                    if dep not in service_catalog:
                         if "db" in dep:
                            mermaid_code.append(f"    class {dep} db;")
                         else:
                            mermaid_code.append(f"    class {dep} unknown;")

                # Style current node
                if "db" in name:
                    mermaid_code.append(f"    class {name} db;")
                elif details.get("tier") == "Tier-1":
                    mermaid_code.append(f"    class {name} tier1;")
                else:
                    mermaid_code.append(f"    class {name} service;")

        # Wrap in markdown block
        return "Here is the topology diagram:\n\n```mermaid\n" + "\n".join(mermaid_code) + "\n```"
    finally:
        db.close()
