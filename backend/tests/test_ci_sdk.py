
import pytest
from unittest.mock import MagicMock, patch
import os
import requests
from backend.app.tools.real import analyze_ci_failure

def test_analyze_ci_failure_uses_sdk():
    # Mock environment variables
    with patch.dict("os.environ", {"GITHUB_TOKEN": "fake-token"}):

        # Patch requests.get globally
        with patch("requests.get") as mock_get:

            # Mock job list response
            mock_jobs_resp = MagicMock()
            mock_jobs_resp.status_code = 200
            mock_jobs_resp.json.return_value = {
                "jobs": [{"id": 123, "name": "Build", "conclusion": "failure"}]
            }

            # Mock log response
            mock_log_resp = MagicMock()
            mock_log_resp.status_code = 200
            mock_log_resp.text = "LONG LOG CONTENT ... ERROR: Something failed."

            # Side effect for requests.get
            mock_get.side_effect = [mock_jobs_resp, mock_log_resp]

            # Mock Google SDK Client
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.text = "Gemini found the error."
            mock_client.models.generate_content.return_value = mock_response

            # Patch get_google_sdk_client in real.py
            with patch("backend.app.tools.real.get_google_sdk_client", return_value=mock_client) as mock_get_client:

                result = analyze_ci_failure.invoke({"build_id": "999", "repo_name": "test-repo"})

                # Verify SDK was used
                mock_get_client.assert_called_once()
                mock_client.models.generate_content.assert_called_once()

                assert "Gemini Analysis" in result

def test_analyze_ci_failure_fallback():
    # Same setup but SDK returns None
    with patch.dict("os.environ", {"GITHUB_TOKEN": "fake-token"}):
        with patch("requests.get") as mock_get:
            mock_jobs_resp = MagicMock()
            mock_jobs_resp.status_code = 200
            mock_jobs_resp.json.return_value = {
                "jobs": [{"id": 123, "name": "Build", "conclusion": "failure"}]
            }
            mock_log_resp = MagicMock()
            mock_log_resp.status_code = 200
            mock_log_resp.text = "Logs..."
            mock_get.side_effect = [mock_jobs_resp, mock_log_resp]

            # Mock SDK as None
            with patch("backend.app.tools.real.get_google_sdk_client", return_value=None):
                # Mock Standard LLM
                with patch("backend.app.tools.real.get_llm") as mock_get_llm:
                    mock_llm = MagicMock()
                    mock_llm.invoke.return_value.content = "Standard LLM Analysis"
                    mock_get_llm.return_value = mock_llm

                    result = analyze_ci_failure.invoke({"build_id": "999", "repo_name": "test-repo"})

                    assert "AI Analysis (Standard)" in result
