import pytest
from unittest.mock import MagicMock
from unittest.mock import patch
from app.tools.bits_ai import bits_ai_investigate_monitor
from app.tools.incidentfox import incidentfox_auto_investigate

def test_bits_ai_investigate_monitor():
    """Verifies that the bits_ai_investigate_monitor returns expected markdown output."""
    mock_metrics = "Metrics: CPU is 95%"
    mock_alerts = "Alerts: High CPU Usage"
    mock_logs = "Logs: Process out of memory"
    mock_diagnosis = "Diagnosis: The service is experiencing high load causing OOM."

    with patch("app.tools.real.get_datadog_metrics") as mock_metrics_tool, \
         patch("app.tools.real.get_active_alerts") as mock_alerts_tool, \
         patch("app.tools.real.get_pod_logs") as mock_logs_tool, \
         patch("app.llm.generate_diagnosis", return_value=mock_diagnosis):

         mock_metrics_tool.invoke = MagicMock(return_value=mock_metrics)
         mock_alerts_tool.invoke = MagicMock(return_value=mock_alerts)
         mock_logs_tool.invoke = MagicMock(return_value=mock_logs)

         # We must mock the actual tools imported into the bits_ai namespace.
         # Because they are imported inside the function, patching them where they are defined (app.tools.real)
         # is effective before they are dynamically imported.

         result = bits_ai_investigate_monitor.invoke({"monitor_query": "high cpu", "service_name": "payment-api"})

         assert "Bits AI SRE Copilot Investigation" in result
         assert "high cpu" in result
         assert mock_diagnosis in result


def test_incidentfox_auto_investigate():
    """Verifies that the incidentfox_auto_investigate returns expected markdown output and Slack notification."""
    mock_investigation = "Investigation: Service is down. DB connections maxed out."
    mock_summary = "Summary: Database connection pool exhausted."
    mock_slack = "Slack Notification Sent to #incidents"

    with patch("app.tools.observability.investigate_root_cause") as mock_investigation_tool, \
         patch("app.llm.generate_diagnosis", return_value=mock_summary), \
         patch("app.tools.real.send_slack_notification") as mock_slack_tool:

         mock_investigation_tool.invoke = MagicMock(return_value=mock_investigation)
         mock_slack_tool.invoke = MagicMock(return_value=mock_slack)

         result = incidentfox_auto_investigate.invoke({"incident_context": "P1 Alert: payment-api down", "service_name": "payment-api"})

         assert "IncidentFox Auto-Investigation Complete" in result
         assert mock_summary in result
