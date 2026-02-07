import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Ensure backend/app is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.tools.incident import generate_remediation_plan
# Mock app.llm functions
with patch("app.llm.get_google_sdk_client") as mock_sdk, \
     patch("app.llm.get_llm") as mock_llm:
     pass

class TestRemediation(unittest.TestCase):
    @patch("app.tools.incident.get_google_sdk_client")
    def test_generate_remediation_plan_sdk(self, mock_get_client):
        # Setup mock client
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Step 1: Restart Pod"
        # The tool calls client.models.generate_content
        mock_client.models.generate_content.return_value = mock_response

        mock_get_client.return_value = mock_client

        # Invoke the tool
        # Note: LangChain tools pass arguments as dict or string
        result = generate_remediation_plan.invoke({"incident_context": "Pod crashing with OOM"})

        # Assertions
        # Since we mocked the SDK, we expect the output to contain the mocked text
        # But we need to see what the tool actually returns.
        # The tool implementation: return f"**Generated Remediation Plan (Gemini):**\n\n{response.text}"

        self.assertIn("Generated Remediation Plan (Gemini)", result)
        self.assertIn("Step 1: Restart Pod", result)

    @patch("app.tools.incident.get_google_sdk_client")
    @patch("app.tools.incident.get_llm")
    def test_generate_remediation_plan_fallback(self, mock_get_llm, mock_get_client):
        # Simulate no SDK client
        mock_get_client.return_value = None

        # Mock LLM fallback
        mock_llm_instance = MagicMock()
        mock_res = MagicMock()
        mock_res.content = "Step 1: Check logs"
        mock_llm_instance.invoke.return_value = mock_res
        mock_get_llm.return_value = mock_llm_instance

        result = generate_remediation_plan.invoke({"incident_context": "DB slow"})

        self.assertIn("Generated Remediation Plan", result)
        self.assertIn("Step 1: Check logs", result)

if __name__ == '__main__':
    unittest.main()
