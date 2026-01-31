import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from unittest.mock import MagicMock, patch
from app.tools.dashboard import analyze_infrastructure_health

def test_dashboard():
    print("Testing analyze_infrastructure_health...")

    # Mock the tools imported inside dashboard.py
    # We patch the tool objects themselves.

    with patch('app.tools.dashboard.list_k8s_pods') as mock_k8s, \
         patch('app.tools.dashboard.get_cluster_events') as mock_events, \
         patch('app.tools.dashboard.check_gcp_status') as mock_gcp, \
         patch('app.tools.dashboard.get_active_alerts') as mock_dd, \
         patch('app.tools.dashboard.check_azion_edge') as mock_azion:

        # Configure mocks to simulate successful .invoke()
        mock_k8s.invoke.return_value = "pod-1 (Running), pod-2 (Running)"
        mock_events.invoke.return_value = "Normal: Started container"
        mock_gcp.invoke.return_value = "GCP Active Projects: my-project..."
        mock_dd.invoke.return_value = "No active alerts."
        mock_azion.invoke.return_value = "Azion Active. Found 3 apps."

        # Run the tool
        # Note: analyze_infrastructure_health is a StructuredTool, so we call invoke
        result = analyze_infrastructure_health.invoke({})

        print("\n--- Dashboard Output ---")
        print(result)
        print("------------------------\n")

        # Assertions
        assert "Relatório de Integridade" in result
        assert "✅ Operacional" in result
        assert "pod-1 (Running)" in result
        assert "GCP Active Projects" in result
        assert "✅ Silencioso" in result  # Datadog
        assert "✅ Online" in result # Azion

    print("Test Passed!")

if __name__ == "__main__":
    test_dashboard()
