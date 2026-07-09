import os
import pytest
from unittest.mock import patch, MagicMock
from app.tools.azion import (
    check_azion_status,
    list_edge_applications,
    purge_azion_cache,
    get_azion_metrics
)

@patch.dict(os.environ, {"AZION_TOKEN": "test_token"})
@patch("app.tools.azion.requests.get")
def test_check_azion_status_success(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"count": 5}
    mock_get.return_value = mock_response

    result = check_azion_status.invoke({})

    assert "Azion Edge CDN is Active" in result
    assert "5 edge applications found" in result
    mock_get.assert_called_once_with(
        "https://api.azionapi.net/edge_applications",
        headers={"Authorization": "Token test_token", "Accept": "application/json; version=3", "Content-Type": "application/json"},
        timeout=10
    )

@patch.dict(os.environ, {"AZION_TOKEN": ""}, clear=True)
def test_check_azion_status_missing_token():
    result = check_azion_status.invoke({})
    assert "Azion Error: AZION_TOKEN is missing" in result

@patch.dict(os.environ, {"AZION_TOKEN": "test_token"})
@patch("app.tools.azion.requests.get")
def test_list_edge_applications_success(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"results": [{"name": "My App", "id": 123}]}
    mock_get.return_value = mock_resp

    result = list_edge_applications.invoke({})
    assert "My App" in result
    assert "123" in result

@patch.dict(os.environ, {"AZION_TOKEN": "test_token"})
@patch("app.tools.azion.requests.post")
def test_purge_azion_cache_success(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    result = purge_azion_cache.invoke({"urls": "http://example.com/1, http://example.com/2 "})

    assert "Successfully purged cache for 2 URL(s)" in result
    mock_post.assert_called_once_with(
        "https://api.azionapi.net/purge/url",
        json={"urls": ["http://example.com/1", "http://example.com/2"], "method": "delete"},
        headers={"Authorization": "Token test_token", "Accept": "application/json; version=3", "Content-Type": "application/json"},
        timeout=10
    )

@patch.dict(os.environ, {"AZION_TOKEN": ""}, clear=True)
def test_purge_azion_cache_missing_token():
    result = purge_azion_cache.invoke({"urls": "http://example.com"})
    assert "Azion Error: AZION_TOKEN is missing" in result

@patch.dict(os.environ, {"AZION_TOKEN": "test_token"})
def test_purge_azion_cache_no_urls():
    result = purge_azion_cache.invoke({"urls": " ,  , "})
    assert "No URLs provided" in result

@patch.dict(os.environ, {"AZION_TOKEN": "test_token"})
@patch("app.tools.azion.requests.post")
def test_get_azion_metrics_success(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_post.return_value = mock_resp

    result = get_azion_metrics.invoke({"app_id": "123", "metric_type": "bandwidth"})
    assert "Azion Metrics for App 123" in result
    assert "bandwidth is normal" in result