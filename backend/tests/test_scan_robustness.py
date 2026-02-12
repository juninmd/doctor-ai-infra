
import pytest
from unittest.mock import MagicMock, patch
import json
import sys

# Mock modules
sys_modules = {
    "kubernetes": MagicMock(),
    "google.cloud": MagicMock(),
    "google.cloud.resourcemanager_v3": MagicMock(),
    "datadog_api_client": MagicMock(),
}
with patch.dict("sys.modules", sys_modules):
    from app.tools import observability

def test_scan_infrastructure_robustness():
    # Patch at the source where observability.py imports FROM
    # It does: from app.tools import list_k8s_pods
    # So we patch app.tools.list_k8s_pods

    with patch("app.tools.list_k8s_pods") as mock_k8s, \
         patch("app.tools.check_gcp_status") as mock_gcp, \
         patch("app.tools.query_gmp_prometheus") as mock_gmp, \
         patch("app.tools.get_active_alerts") as mock_dd, \
         patch("app.tools.check_azion_edge") as mock_azion:

        # Configure mocks
        # K8s raises exception
        mock_k8s.invoke.side_effect = Exception("K8s Connection Failed")

        # GCP returns success
        mock_gcp.invoke.return_value = "GCP Active"

        # GMP raises exception
        mock_gmp.invoke.side_effect = Exception("GMP Timeout")

        # Datadog returns success
        mock_dd.invoke.return_value = "No active alerts"

        # Azion returns success
        mock_azion.invoke.return_value = "Azion Active"

        # Run scan
        result = observability.scan_infrastructure.invoke({})

        # Verify JSON block exists
        assert "```json" in result

        # Extract and parse JSON
        json_str = result.split("```json")[1].split("```")[0].strip()
        data = json.loads(json_str)

        # Assert structure
        assert data["k8s"]["status"] == "error"
        assert "K8s Connection Failed" in data["k8s"]["msg"]

        assert data["gcp"]["status"] == "healthy"

        assert data["gmp"]["status"] == "error"
        assert "GMP Timeout" in data["gmp"]["msg"]

        assert data["datadog"]["status"] == "healthy"
