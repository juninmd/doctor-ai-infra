import pytest
from unittest.mock import patch, MagicMock
from app.tools.azion import (
    check_azion_status,
    list_edge_applications,
    purge_azion_cache,
    get_azion_metrics
)
import os

@patch.dict(os.environ, {"AZION_TOKEN": "fake-token"})
@patch("app.tools.azion.requests.get")
def test_check_azion_status_success(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_get.return_value = mock_resp

    result = check_azion_status.invoke({})
    assert "🟢 Healthy" in result

@patch.dict(os.environ, {"AZION_TOKEN": ""})
def test_check_azion_status_missing_token():
    result = check_azion_status.invoke({})
    assert "Azion Error" in result
    assert "AZION_TOKEN is missing" in result

@patch.dict(os.environ, {"AZION_TOKEN": "fake-token"})
@patch("app.tools.azion.requests.get")
def test_list_edge_applications_success(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"results": [{"name": "My App", "id": 123}]}
    mock_get.return_value = mock_resp

    result = list_edge_applications.invoke({})
    assert "My App" in result
    assert "123" in result

@patch.dict(os.environ, {"AZION_TOKEN": "fake-token"})
@patch("app.tools.azion.requests.post")
def test_purge_azion_cache_success(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 201
    mock_post.return_value = mock_resp

    result = purge_azion_cache.invoke({"urls": ["http://example.com/api/*"]})
    assert "Successfully purged 1 URL(s)" in result
    mock_post.assert_called_once()
    assert mock_post.call_args[1]["json"] == {"urls": ["http://example.com/api/*"]}

@patch.dict(os.environ, {"AZION_TOKEN": "fake-token"})
@patch("app.tools.azion.requests.post")
def test_get_azion_metrics_success(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_post.return_value = mock_resp

    result = get_azion_metrics.invoke({"app_id": "123", "metric_type": "bandwidth"})
    assert "Azion Metrics for App 123" in result
    assert "bandwidth is normal" in result
