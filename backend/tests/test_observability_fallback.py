import pytest
from unittest.mock import MagicMock, patch
import json
import sys

sys_modules = {
    "kubernetes": MagicMock(),
    "google.cloud": MagicMock(),
    "google.cloud.resourcemanager_v3": MagicMock(),
    "datadog_api_client": MagicMock(),
}

with patch.dict("sys.modules", sys_modules):
    from app.tools import observability

def test_scan_infrastructure_fallback_to_standard_llm():
    with patch("app.tools.list_k8s_pods") as mock_k8s, \
         patch("app.tools.check_gcp_status") as mock_gcp, \
         patch("app.tools.query_gmp_prometheus") as mock_gmp, \
         patch("app.tools.get_active_alerts") as mock_dd, \
         patch("app.tools.check_traefik_health") as mock_traefik, \
         patch("app.llm.get_google_sdk_client") as mock_get_sdk, \
         patch("app.llm.get_llm") as mock_get_llm:

        mock_k8s.invoke.return_value = "K8s: All systems go"
        mock_gcp.invoke.return_value = "GCP: Stable"
        mock_gmp.invoke.return_value = "GMP: Metrics normal"
        mock_dd.invoke.return_value = "Datadog: No alerts"
        mock_traefik.invoke.return_value = "🟢 Traefik: OK"

        mock_get_sdk.return_value = None
        mock_llm_instance = MagicMock()
        mock_llm_instance.invoke.return_value = MagicMock(content="Fallback Insight: System looks good running on local LLM.")
        mock_get_llm.return_value = mock_llm_instance

        result = observability.scan_infrastructure.invoke({})

        mock_get_sdk.assert_called()
        mock_get_llm.assert_called()
        mock_llm_instance.invoke.assert_called()
        assert "Fallback Insight: System looks good running on local LLM." in result
