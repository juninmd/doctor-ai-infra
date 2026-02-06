import unittest
from unittest.mock import MagicMock, patch
import os
import datetime
# Import the tool object, we will access the underlying function for easier testing or use invoke
from app.tools.real import analyze_gcp_errors

class TestGCPErrors(unittest.TestCase):
    @patch("app.tools.real.cloud_logging")
    @patch("app.tools.real.default")
    @patch.dict(os.environ, {"GOOGLE_CLOUD_PROJECT": "test-project"})
    def test_analyze_gcp_errors_success(self, mock_default, mock_cloud_logging):
        # Setup mock default auth to return creds and project
        mock_default.return_value = (MagicMock(), "test-project")

        # Mock Client
        mock_client = MagicMock()
        mock_cloud_logging.Client.return_value = mock_client
        mock_cloud_logging.DESCENDING = "DESC"

        # Mock Entries
        entry1 = MagicMock()
        entry1.timestamp = datetime.datetime.now()
        entry1.payload = "Error 1 occurred"

        entry2 = MagicMock()
        entry2.timestamp = datetime.datetime.now()
        entry2.payload = {"message": "Error 2 occurred"}

        mock_client.list_entries.return_value = [entry1, entry2]

        # Use invoke for LangChain tools
        result = analyze_gcp_errors.invoke({"days": 1})

        self.assertIn("Found 2 errors", result)
        self.assertIn("Error 1 occurred", result)
        self.assertIn("Error 2 occurred", result)

        # Verify call args
        mock_client.list_entries.assert_called_once()
        call_kwargs = mock_client.list_entries.call_args[1]
        self.assertIn("severity>=ERROR", call_kwargs['filter_'])

    @patch("app.tools.real.cloud_logging", None)
    def test_analyze_gcp_errors_not_installed(self):
        result = analyze_gcp_errors.invoke({"days": 1})
        self.assertIn("GCP Cloud Logging library not installed", result)

if __name__ == "__main__":
    unittest.main()
