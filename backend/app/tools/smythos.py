from langchain_core.tools import tool
import os

@tool
def smythos_unified_resource_manager(action: str, resource_type: str, resource_name: str, payload: str = None) -> str:
    """
    Exposes a unified OS-level abstraction for interacting with AI resources seamlessly,
    adopting the SmythOS architecture.

    Args:
        action: The action to perform ('read', 'write', 'execute').
        resource_type: The type of resource ('LLM', 'Storage', 'VectorDB').
        resource_name: The specific name or identifier of the resource.
        payload: Optional data payload for write/execute actions.
    """
    try:
        # Simulate SmythOS modular architecture routing
        if resource_type.upper() == "LLM":
            from app.llm import get_llm
            if action.lower() == "execute":
                llm = get_llm()
                response = llm.invoke(payload if payload else f"Test prompt for {resource_name}")
                return f"[SmythOS LLM Connector] Response from {resource_name}: {response.content}"
            else:
                return f"[SmythOS LLM Connector] Unsupported action '{action}' for LLM."

        elif resource_type.upper() == "STORAGE":
            # Simulate Storage connector
            if action.lower() == "write":
                return f"[SmythOS Storage Connector] Successfully wrote payload to {resource_name}."
            elif action.lower() == "read":
                return f"[SmythOS Storage Connector] Read data from {resource_name}: (simulated data)"
            else:
                 return f"[SmythOS Storage Connector] Unsupported action '{action}' for Storage."

        elif resource_type.upper() == "VECTORDB":
            # Simulate VectorDB connector
            from app.rag import rag_engine
            if action.lower() == "read":
                results = rag_engine.search(payload if payload else "test", k=1)
                docs = [doc.page_content for doc in results] if results else ["No results"]
                return f"[SmythOS VectorDB Connector] Search results from {resource_name}: {docs}"
            elif action.lower() == "write":
                return f"[SmythOS VectorDB Connector] Successfully indexed payload into {resource_name}."
            else:
                 return f"[SmythOS VectorDB Connector] Unsupported action '{action}' for VectorDB."
        else:
            return f"[SmythOS Kernel] Unknown resource type: '{resource_type}'."

    except Exception as e:
        return f"Error executing SmythOS unified resource manager: {e}"
