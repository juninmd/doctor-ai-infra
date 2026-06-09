import pytest
from unittest.mock import patch, MagicMock
import os
from app.tools.azion import check_azion_edge, check_azion_waf, purge_azion_cache

def test_check_azion_edge_success():
    with patch.dict(os.environ, {"AZION_TOKEN": "test_token"}):
        with patch("app.tools.azion.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "results": [
                    {"id": 123, "name": "App 1", "active": True}
                ]
            }
            mock_get.return_value = mock_response

            result = check_azion_edge.invoke({})
            assert "Found 1 Azion Edge Applications" in result
            assert "App 1" in result

def test_check_azion_edge_no_token():
    with patch.dict(os.environ, clear=True):
        result = check_azion_edge.invoke({})
        assert "AZION_TOKEN is missing" in result

def test_check_azion_waf_success():
    with patch.dict(os.environ, {"AZION_TOKEN": "test_token"}):
        with patch("app.tools.azion.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "results": [
                    {"id": 456, "name": "WAF 1", "is_active": True}
                ]
            }
            mock_get.return_value = mock_response

            result = check_azion_waf.invoke({})
            assert "Found 1 Azion WAF Configurations" in result
            assert "WAF 1" in result

def test_purge_azion_cache_success():
    with patch.dict(os.environ, {"AZION_TOKEN": "test_token"}):
        with patch("app.tools.azion.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            result = purge_azion_cache.invoke({"urls": "http://example.com/test"})
            assert "Successfully requested cache purge" in result
            mock_post.assert_called_once()
            _, kwargs = mock_post.call_args
            assert kwargs["json"]["urls"] == ["http://example.com/test"]
