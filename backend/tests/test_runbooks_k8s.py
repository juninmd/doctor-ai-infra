
import pytest
from unittest.mock import MagicMock, patch
import sys

# Mock modules to avoid import errors
sys_modules = {
    "kubernetes": MagicMock(),
    "kubernetes.client": MagicMock(),
    "kubernetes.config": MagicMock(),
}
with patch.dict("sys.modules", sys_modules):
    from backend.app.tools import runbooks

def test_execute_runbook_restart_service_k8s():
    # Mock DB Session
    mock_db = MagicMock()
    mock_service = MagicMock()
    mock_service.name = "payment-api"
    # Set runbook association
    mock_rb = MagicMock()
    mock_rb.name = "restart_service"
    mock_service.runbooks = [mock_rb]

    # Simplified Mock Chaining
    mock_query = MagicMock()
    mock_filter = MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter

    # Sequence:
    # 1. query(Service).filter().first() -> mock_service
    # 2. query(Runbook).filter().first() -> mock_rb
    mock_filter.first.side_effect = [mock_service, mock_rb]

    # Mock K8s Client
    mock_k8s_client = MagicMock()
    mock_pod = MagicMock()
    mock_pod.metadata.name = "pod-123"
    # Ensure items is a list
    mock_k8s_client.list_namespaced_pod.return_value.items = [mock_pod]

    with patch("backend.app.tools.runbooks.SessionLocal", return_value=mock_db):
        # Patch the helper functions using object patch on the imported module
        with patch.object(runbooks, "_get_k8s_client", return_value=mock_k8s_client):

            result = runbooks.execute_runbook.invoke({"runbook_name": "restart_service", "target_service": "payment-api"})

            # Assertions
            mock_k8s_client.list_namespaced_pod.assert_called_with("default", label_selector="app=payment-api")
            mock_k8s_client.delete_namespaced_pod.assert_called_with("pod-123", "default")
            assert "Deleted 1 pods" in result

def test_execute_runbook_scale_up_k8s():
    # Mock DB
    mock_db = MagicMock()
    mock_service = MagicMock()
    mock_service.name = "payment-api"
    mock_rb = MagicMock()
    mock_rb.name = "scale_up"
    mock_service.runbooks = [mock_rb]

    # Simplified Mock Chaining
    mock_query = MagicMock()
    mock_filter = MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.first.side_effect = [mock_service, mock_rb]

    # Mock K8s Apps Client
    mock_apps_client = MagicMock()
    mock_deployment = MagicMock()
    mock_deployment.spec.replicas = 2
    mock_apps_client.read_namespaced_deployment.return_value = mock_deployment

    with patch("backend.app.tools.runbooks.SessionLocal", return_value=mock_db):
        with patch.object(runbooks, "_get_k8s_apps_client", return_value=mock_apps_client):

            result = runbooks.execute_runbook.invoke({"runbook_name": "scale_up", "target_service": "payment-api"})

            mock_apps_client.read_namespaced_deployment.assert_called_with("payment-api", "default")
            mock_apps_client.patch_namespaced_deployment.assert_called()

            # Check args for patch
            args, kwargs = mock_apps_client.patch_namespaced_deployment.call_args
            assert args[0] == "payment-api"
            assert args[2] == {"spec": {"replicas": 4}} # 2 + 2

            assert "Scaled 'payment-api' from 2 to 4" in result
