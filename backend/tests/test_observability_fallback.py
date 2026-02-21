import pytest
from unittest.mock import MagicMock, patch
import json
import sys

# 1. Mock external modules to avoid ImportErrors during test collection
sys_modules = {
    "kubernetes": MagicMock(),
    "google.cloud": MagicMock(),
    "google.cloud.resourcemanager_v3": MagicMock(),
    "datadog_api_client": MagicMock(),
}

# 2. Patch sys.modules so imports in observability.py succeed
with patch.dict("sys.modules", sys_modules):
    from app.tools import observability

def test_scan_infrastructure_fallback_to_standard_llm():
    """
    Verifies that scan_infrastructure uses the standard LLM (e.g. Ollama)
    when the Google GenAI SDK client is unavailable (returns None).

    NOTE: This test relies on the fact that `scan_infrastructure` in `observability.py`
    performs LOCAL imports for tools and the SDK client (e.g., `from app.tools import ...`).
    Therefore, patching `app.tools.list_k8s_pods` works because the import happens at runtime,
    resolving to the mocked object. Similarly for `app.llm.get_google_sdk_client`.
    """

    with patch("app.tools.list_k8s_pods") as mock_k8s, \
         patch("app.tools.check_gcp_status") as mock_gcp, \
         patch("app.tools.query_gmp_prometheus") as mock_gmp, \
         patch("app.tools.get_active_alerts") as mock_dd, \
         patch("app.tools.check_azion_edge") as mock_azion, \
         patch("app.llm.get_google_sdk_client") as mock_get_sdk, \
         patch("app.llm.get_llm") as mock_get_llm:

        # Setup Tool Mocks
        mock_k8s.invoke.return_value = "K8s: All systems go"
        mock_gcp.invoke.return_value = "GCP: Stable"
        mock_gmp.invoke.return_value = "GMP: Metrics normal"
        mock_dd.invoke.return_value = "Datadog: No alerts"
        mock_azion.invoke.return_value = "Azion: Edge active"

        # Setup AI Mocks - The core of this test
        # 1. Simulate Google SDK is NOT configured (returns None)
        mock_get_sdk.return_value = None

        # 2. Simulate Standard LLM (Ollama) is available
        mock_llm_instance = MagicMock()
        # The fallback logic should call invoke() on the LLM
        mock_llm_instance.invoke.return_value = MagicMock(content="Fallback Insight: System looks good running on local LLM.")
        mock_get_llm.return_value = mock_llm_instance

        # Execute the function under test
        # invoke() is a method of the Tool object
        result = observability.scan_infrastructure.invoke({})

        # Assertions
        # 1. Verify Google SDK was checked
        mock_get_sdk.assert_called()

        # 2. Verify Standard LLM was retrieved and invoked
        mock_get_llm.assert_called()
        mock_llm_instance.invoke.assert_called()

        # 3. Verify the result contains the text from the fallback LLM
        assert "Fallback Insight: System looks good running on local LLM." in result
        assert "🧠 **AI Insight:** Fallback Insight" in result
