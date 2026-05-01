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

def test_scan_infrastructure_robustness():
    with patch("app.tools.list_k8s_pods") as mock_k8s, \
         patch("app.tools.check_gcp_status") as mock_gcp, \
         patch("app.tools.query_gmp_prometheus") as mock_gmp, \
         patch("app.tools.get_active_alerts") as mock_dd, \
         patch("app.tools.check_traefik_health") as mock_traefik:

        mock_k8s.invoke.side_effect = Exception("K8s Connection Failed")
        mock_gcp.invoke.return_value = "GCP Active"
        mock_gmp.invoke.side_effect = Exception("GMP Timeout")
        mock_dd.invoke.return_value = "No active alerts"
        mock_traefik.invoke.return_value = "🟢 Traefik Active"

        result = observability.scan_infrastructure.invoke({})
        assert "```json" in result
        json_str = result.split("```json")[1].split("```")[0].strip()
        data = json.loads(json_str)

        assert data["k8s"]["status"] == "error"
        assert data["gcp"]["status"] == "healthy"
        assert data["gmp"]["status"] == "error"
        assert data["datadog"]["status"] == "healthy"
        assert data["traefik"]["status"] == "healthy"
