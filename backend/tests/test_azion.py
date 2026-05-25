import os
import pytest
from unittest.mock import patch, MagicMock
from app.tools.azion import check_azion_status, purge_azion_cache

@patch.dict(os.environ, {"AZION_TOKEN": "test_token"})
@patch("app.tools.azion.requests.get")
def test_check_azion_status_success(mock_get):
    """Verifies check_azion_status returns active count correctly."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"count": 5}
    mock_get.return_value = mock_response

    result = check_azion_status.invoke({})

    assert "Azion Edge CDN is Active" in result
    assert "5 edge applications found" in result
    mock_get.assert_called_once_with(
        "https://api.azionapi.net/edge_applications",
        headers={"Authorization": "Token test_token", "Accept": "application/json"},
        timeout=10
    )

@patch.dict(os.environ, {"AZION_TOKEN": ""}, clear=True)
def test_check_azion_status_missing_token():
    """Verifies check_azion_status handles missing token."""
    result = check_azion_status.invoke({})
    assert "Error: AZION_TOKEN missing" in result

@patch.dict(os.environ, {"AZION_TOKEN": "test_token"})
@patch("app.tools.azion.requests.post")
def test_purge_azion_cache_success(mock_post):
    """Verifies purge_azion_cache handles valid URLs correctly."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    result = purge_azion_cache.invoke({"urls": "http://example.com/1, http://example.com/2 "})

    assert "Successfully purged cache for 2 URL(s)" in result
    mock_post.assert_called_once_with(
        "https://api.azionapi.net/purge/url",
        json={"urls": ["http://example.com/1", "http://example.com/2"], "method": "delete"},
        headers={"Authorization": "Token test_token", "Accept": "application/json", "Content-Type": "application/json"},
        timeout=10
    )

@patch.dict(os.environ, {"AZION_TOKEN": ""}, clear=True)
def test_purge_azion_cache_missing_token():
    """Verifies purge_azion_cache handles missing token."""
    result = purge_azion_cache.invoke({"urls": "http://example.com"})
    assert "Error: AZION_TOKEN missing" in result

@patch.dict(os.environ, {"AZION_TOKEN": "test_token"})
def test_purge_azion_cache_no_urls():
    """Verifies purge_azion_cache handles empty or blank URLs."""
    result = purge_azion_cache.invoke({"urls": " ,  , "})
    assert "No URLs provided" in result
