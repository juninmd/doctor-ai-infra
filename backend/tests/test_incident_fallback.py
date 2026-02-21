import pytest
from unittest.mock import MagicMock, patch
import sys

# Mock sys.modules to avoid side effects or database connections during import
sys_modules = {
    "app.db": MagicMock(),
    # "app.rag": MagicMock(),
}

with patch.dict("sys.modules", sys_modules):
    # Mock app.rag.rag_engine to avoid initialization
    with patch("app.rag.rag_engine", MagicMock()):
        from app.tools import incident

def test_generate_remediation_plan_fallback():
    """
    Verifies that generate_remediation_plan uses the standard LLM (e.g. Ollama)
    when the Google GenAI SDK client is unavailable.
    """

    # Use patch.object on the imported module directly to avoid resolution issues
    with patch.object(incident, "get_google_sdk_client") as mock_get_sdk, \
         patch.object(incident, "get_llm") as mock_get_llm:

        # 1. Simulate Google SDK is NOT configured (returns None)
        mock_get_sdk.return_value = None

        # 2. Simulate Standard LLM (Ollama) is available
        mock_llm_instance = MagicMock()
        mock_llm_instance.invoke.return_value = MagicMock(content="Standard Remediation Plan")
        mock_get_llm.return_value = mock_llm_instance

        # Execute
        result = incident.generate_remediation_plan.invoke({"incident_context": "Service Down"})

        # Assertions
        # 1. Verify SDK check
        mock_get_sdk.assert_called()

        # 2. Verify Fallback LLM usage
        mock_get_llm.assert_called()
        mock_llm_instance.invoke.assert_called()

        # 3. Check Result Content
        assert "Standard Remediation Plan" in result
        assert "Generated Remediation Plan:" in result
        # Ensure Gemini signature is NOT present
        assert "(Gemini)" not in result
