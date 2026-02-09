import unittest
from unittest.mock import MagicMock, patch
# We must import the tool function.
# Since it's decorated with @tool, analyze_log_patterns is a Runnable/Tool, but typical usage as function works if configured.
# However, inside real.py it is decorated.
# Let's import the module to patch properly.
from app.tools import real

class TestLogAnalysis(unittest.TestCase):

    @patch('app.tools.real.get_pod_logs')
    @patch('app.tools.real.get_google_sdk_client')
    def test_gemini_sdk_path(self, mock_get_sdk, mock_get_pod_logs_tool):
        # Setup
        # analyze_log_patterns calls get_pod_logs.invoke(...)
        mock_get_pod_logs_tool.invoke.return_value = "ERROR: Connection failed\nStacktrace..." + (" " * 50)

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Gemini Analysis: Database is down."
        mock_client.models.generate_content.return_value = mock_response
        mock_get_sdk.return_value = mock_client

        # Execute
        # Note: analyze_log_patterns is a tool, so we invoke it or call it if it's a function.
        # LangChain @tool makes it a StructuredTool. We must invoke it with a dict.
        result = real.analyze_log_patterns.invoke({"pod_name": "my-pod"})

        # Verify
        self.assertIn("**AI Log Analysis (Gemini 1.5 Flash):**", result)
        self.assertIn("Database is down", result)
        mock_client.models.generate_content.assert_called_once()

    @patch('app.tools.real.get_pod_logs')
    @patch('app.tools.real.get_google_sdk_client')
    @patch('app.tools.real.get_llm')
    def test_ollama_fallback_path(self, mock_get_llm, mock_get_sdk, mock_get_pod_logs_tool):
        # Setup
        mock_get_pod_logs_tool.invoke.return_value = "ERROR: Timeout\nStacktrace..." + (" " * 50)
        mock_get_sdk.return_value = None # Simulate no SDK/API Key

        mock_llm = MagicMock()
        mock_res = MagicMock()
        mock_res.content = "Ollama Analysis: Network issue."
        mock_llm.invoke.return_value = mock_res
        mock_get_llm.return_value = mock_llm

        # Execute
        result = real.analyze_log_patterns.invoke({"pod_name": "my-pod"})

        # Verify
        self.assertIn("**AI Log Analysis (Standard LLM):**", result)
        self.assertIn("Network issue", result)
        mock_llm.invoke.assert_called_once()
