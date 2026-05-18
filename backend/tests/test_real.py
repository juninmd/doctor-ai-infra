import pytest
from unittest.mock import patch, MagicMock
from app.tools.real import (
    list_k8s_pods,
    check_gcp_status,
    get_active_alerts
)
import os

def test_list_k8s_pods_success():
    """Test successful k8s pod listing."""
    with patch('app.tools.real.config.load_kube_config'), \
         patch('app.tools.real.client.CoreV1Api') as mock_api:
        mock_v1 = MagicMock()
        mock_pod = MagicMock()
        mock_pod.metadata.name = "test-pod-1"
        mock_pod.status.phase = "Running"
        mock_v1.list_namespaced_pod.return_value.items = [mock_pod]
        mock_api.return_value = mock_v1
        result = list_k8s_pods.invoke({"namespace": "default"})
        assert "test-pod-1" in result
        assert "Running" in result

def test_list_k8s_pods_failure():
    """Test k8s pod listing failure."""
    # We patch the internal helper rather than the config methods, since real handles the exceptions
    # inside _get_k8s_client
    with patch('app.tools.real._get_k8s_client', return_value=None):
        result = list_k8s_pods.invoke({"namespace": "default"})
        assert "Error: Could not load Kubernetes configuration" in result

def test_check_gcp_status_success():
    """Test GCP status check."""
    mock_rm = MagicMock()
    mock_client = MagicMock()
    mock_project = MagicMock()
    mock_project.project_id = "test-project-1"
    mock_client.list_projects.return_value = [mock_project]
    mock_rm.ProjectsClient.return_value = mock_client
    with patch('app.tools.real.resourcemanager_v3', mock_rm):
        result = check_gcp_status.invoke({})
        assert "GCP Connection Successful" in result
        assert "test-project-1" in result

def test_get_active_alerts_success():
    """Test Datadog alerts."""
    os.environ["DD_API_KEY"] = "fake-api"
    os.environ["DD_APP_KEY"] = "fake-app"
    mock_monitors_api = MagicMock()
    mock_monitor = MagicMock()
    mock_monitor.name = "High CPU"
    mock_monitor.overall_state = "Alert"
    mock_monitors_api_instance = MagicMock()
    mock_monitors_api_instance.list_monitors.return_value = [mock_monitor]
    mock_monitors_api.return_value = mock_monitors_api_instance
    with patch('app.tools.real.ApiClient', create=True), \
         patch('app.tools.real.MonitorsApi', mock_monitors_api, create=True), \
         patch('app.tools.real.Configuration', create=True):
            result = get_active_alerts.invoke({})
            assert "High CPU" in result
