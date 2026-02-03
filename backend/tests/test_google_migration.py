import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Ensure backend path is in sys.path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.llm import get_llm, get_google_sdk_client
from app.tools.observability import analyze_heavy_logs

class TestGoogleMigration(unittest.TestCase):
    def setUp(self):
        # Mock env vars
        self.env_patcher = patch.dict(os.environ, {
            "GOOGLE_API_KEY": "fake_key",
            "LLM_PROVIDER": "gemini"
        })
        self.env_patcher.start()

    def tearDown(self):
        self.env_patcher.stop()

    def test_llm_instantiation(self):
        print("Testing LLM instantiation with Gemini config...")
        llm = get_llm()
        self.assertIsNotNone(llm)
        from langchain_google_genai import ChatGoogleGenerativeAI
        self.assertIsInstance(llm, ChatGoogleGenerativeAI)
        self.assertEqual(llm.temperature, 0)
        print("LLM instantiated successfully.")

    def test_google_sdk_client(self):
        print("Testing Google SDK Client access...")
        # We need to verify that get_google_sdk_client returns a client.
        # Since google-genai is installed, we can let it run.
        # If Client() validates the key immediately, this might fail, so we might need to patch the Client class.

        # We patch 'google.genai.Client' where it is defined.
        # But 'app.llm' imports 'genai' module. So 'app.llm.genai.Client' is the target?
        # No, app.llm has 'from google import genai'.
        # We need to patch 'google.genai.Client'.

        with patch("google.genai.Client") as MockClient:
            client = get_google_sdk_client()
            self.assertIsNotNone(client)
            MockClient.assert_called_with(api_key="fake_key")

        print("Google SDK Client retrieved successfully.")

    @patch("app.llm.get_google_sdk_client")
    def test_analyze_heavy_logs(self, mock_get_client):
        print("Testing analyze_heavy_logs tool...")
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Analysis complete: Root cause is DNS."
        mock_client.models.generate_content.return_value = mock_response
        mock_get_client.return_value = mock_client

        result = analyze_heavy_logs.invoke({"log_content": "Error: connection failed", "context": "test"})

        self.assertIn("Gemini Analysis", result)
        self.assertIn("Root cause is DNS", result)
        print("analyze_heavy_logs tool verified.")

if __name__ == "__main__":
    unittest.main()
