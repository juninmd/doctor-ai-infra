import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Ensure backend/app is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.llm import get_google_sdk_client, get_llm
import google.genai # Make sure it is loaded for patching

class TestGoogleGenAISDK(unittest.TestCase):
    def setUp(self):
        self.original_api_key = os.environ.get("GOOGLE_API_KEY")
        os.environ["GOOGLE_API_KEY"] = "fake-api-key"

    def tearDown(self):
        if self.original_api_key:
            os.environ["GOOGLE_API_KEY"] = self.original_api_key
        else:
            del os.environ["GOOGLE_API_KEY"]

    def test_get_google_sdk_client_success(self):
        """Test that get_google_sdk_client returns a client when API key is present."""
        # Patch google.genai.Client
        with patch("google.genai.Client") as MockClient:
            mock_instance = MagicMock()
            MockClient.return_value = mock_instance

            client = get_google_sdk_client()

            # Verify it called genai.Client with the key
            MockClient.assert_called_once_with(api_key="fake-api-key")
            self.assertEqual(client, mock_instance)

    @patch("app.llm.ChatGoogleGenerativeAI")
    def test_get_llm_gemini(self, mock_chat_google):
        """Test that get_llm uses langchain-google-genai with correct settings."""
        os.environ["LLM_PROVIDER"] = "gemini"

        get_llm()

        # Verify it was called with model="gemini-1.5-flash"
        mock_chat_google.assert_called_once()
        call_args = mock_chat_google.call_args[1]
        self.assertEqual(call_args["model"], "gemini-1.5-flash")
        self.assertEqual(call_args["google_api_key"], "fake-api-key")
        self.assertIn("safety_settings", call_args)

if __name__ == '__main__':
    unittest.main()
