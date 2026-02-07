import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Ensure backend/app is in path
sys.path.append('/app/backend')

from app.tools.observability import investigate_root_cause, scan_infrastructure

class TestObservability(unittest.TestCase):
    @patch("app.tools.observability.analyze_heavy_logs")
    @patch("app.tools.observability.concurrent.futures.ThreadPoolExecutor")
    def test_investigate_root_cause_calls_ai(self, mock_executor, mock_analyze):
        # Mock executor result
        mock_future = MagicMock()
        mock_future.result.return_value = "Mock Data"
        mock_executor.return_value.__enter__.return_value.submit.return_value = mock_future

        # When mocking a Tool, invoke() is called.
        mock_analyze.invoke.return_value = "AI Summary: 90% DB issue"

        result = investigate_root_cause.invoke({"service_name": "my-service"})

        self.assertIn("[AI ROOT CAUSE ANALYSIS]", result)
        self.assertIn("AI Summary: 90% DB issue", result)
        mock_analyze.invoke.assert_called_once()

    @patch("app.tools.observability.concurrent.futures.ThreadPoolExecutor")
    def test_scan_infrastructure_json(self, mock_executor):
        # Mock executor result
        mock_future = MagicMock()
        mock_future.result.return_value = "Running"
        mock_executor.return_value.__enter__.return_value.submit.return_value = mock_future

        result = scan_infrastructure.invoke({})

        self.assertIn("Infrastructure Scan Report:", result)
        self.assertIn("```json", result)
        self.assertIn('"k8s":', result)

if __name__ == '__main__':
    unittest.main()
