import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, UTC
from app.tools import knowledge, incident, real

class TestBestOf2026Features(unittest.TestCase):

    @patch('app.tools.knowledge.SessionLocal')
    def test_generate_service_catalog_docs(self, mock_session_local):
        """
        Verifies that generate_service_catalog_docs produces valid Markdown documentation.
        """
        # Setup Mock DB
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        # Create Mock Services
        s1 = MagicMock()
        s1.name = "payment-api"
        s1.owner = "Team Checkout"
        s1.tier = "Tier-1"
        s1.description = "Handles payments."
        s1.telemetry_url = "http://telemetry/payment"
        s1.dependencies = []
        s1.runbooks = []

        s2 = MagicMock()
        s2.name = "auth-service"
        s2.owner = "Team Auth"
        s2.tier = "Tier-0"
        s2.description = "Handles login."
        s2.telemetry_url = None
        # s2 depends on s1 (circular but fine for mock)
        dep = MagicMock()
        dep.name = "payment-api"
        s2.dependencies = [dep]

        # Add runbook to s2
        rb = MagicMock()
        rb.name = "restart_auth"
        rb.description = "Restarts auth service"
        s2.runbooks = [rb]

        mock_db.query.return_value.all.return_value = [s1, s2]

        # Execute
        docs = knowledge.generate_service_catalog_docs.invoke({})

        # Verify Markdown Structure
        self.assertIn("# 📖 Service Catalog Documentation", docs)
        self.assertIn("## 🏗️ payment-api", docs)
        self.assertIn("- **Owner:** Team Checkout", docs)
        self.assertIn("## 🏗️ auth-service", docs)
        self.assertIn("- **restart_auth**: Restarts auth service", docs)
        self.assertIn("### Dependencies", docs)
        # Check dependency link
        self.assertIn("- payment-api", docs)

    @patch('app.tools.incident.SessionLocal')
    def test_build_incident_timeline_mermaid(self, mock_session_local):
        """
        Verifies that build_incident_timeline generates correct Mermaid Gantt chart syntax.
        """
        # Setup Mock DB
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_inc = MagicMock()
        mock_inc.id = "inc-123"
        mock_inc.title = "Database Outage"

        # Mock query(Incident).filter(...).first()
        mock_query_inc = MagicMock()
        mock_query_inc.filter.return_value.first.return_value = mock_inc

        # Mock query(IncidentEvent)...all()
        e1 = MagicMock()
        e1.event_type = "Creation"
        e1.source = "System"
        e1.content = "Incident created"
        e1.created_at = datetime(2026, 5, 20, 10, 0, 0, tzinfo=UTC)

        e2 = MagicMock()
        e2.event_type = "Action"
        e2.source = "K8s_Specialist"
        e2.content = "Scaled up replicas"
        e2.created_at = datetime(2026, 5, 20, 10, 5, 0, tzinfo=UTC)

        mock_query_events = MagicMock()
        # Side effect for query calls: first call returns incident query, second returns events query
        # But here we mocking based on call order or property access
        # The tool calls: db.query(Incident) then db.query(IncidentEvent)

        def side_effect(model):
            if model == incident.Incident:
                return mock_query_inc
            if model == incident.IncidentEvent:
                return mock_query_events
            return MagicMock()

        mock_db.query.side_effect = side_effect
        mock_query_events.filter.return_value.order_by.return_value.all.return_value = [e1, e2]

        # Execute
        result = incident.build_incident_timeline.invoke({"incident_id": "inc-123", "format": "mermaid"})

        # Verify Mermaid Syntax
        self.assertIn("```mermaid", result)
        self.assertIn("gantt", result)
        self.assertIn("title Incident Timeline: Database Outage", result)
        self.assertIn("section Incident inc-123", result)
        self.assertIn("Creation (System) - Incident created :milestone, 2026-05-20 10:00:00, 0m", result)
        self.assertIn("Action (K8s_Specialist) - Scaled up replicas :milestone, 2026-05-20 10:05:00, 0m", result)

    @patch('app.tools.incident.get_google_sdk_client')
    def test_generate_remediation_plan_gemini(self, mock_get_sdk):
        """
        Verifies generate_remediation_plan uses Gemini SDK when available.
        """
        # Setup Mock Gemini
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "- Step 1: Check logs\n- Step 2: Restart pod"
        mock_client.models.generate_content.return_value = mock_response
        mock_get_sdk.return_value = mock_client

        # Execute
        plan = incident.generate_remediation_plan.invoke({"incident_context": "Pod crashing with OOMKilled"})

        # Verify
        self.assertIn("**Generated Remediation Plan (Gemini):**", plan)
        self.assertIn("- Step 1: Check logs", plan)
        mock_client.models.generate_content.assert_called_once()
        # Verify model name
        args, kwargs = mock_client.models.generate_content.call_args
        self.assertEqual(kwargs['model'], "gemini-1.5-flash")

    @patch('app.tools.incident.get_google_sdk_client')
    @patch('app.tools.incident.get_llm')
    def test_generate_remediation_plan_fallback(self, mock_get_llm, mock_get_sdk):
        """
        Verifies generate_remediation_plan falls back to standard LLM when Gemini SDK is unavailable.
        """
        # Setup
        mock_get_sdk.return_value = None # No SDK

        mock_llm = MagicMock()
        mock_res = MagicMock()
        mock_res.content = "- Step 1: Check logs (Ollama)"
        mock_llm.invoke.return_value = mock_res
        mock_get_llm.return_value = mock_llm

        # Execute
        plan = incident.generate_remediation_plan.invoke({"incident_context": "Pod crashing"})

        # Verify
        self.assertIn("**Generated Remediation Plan:**", plan) # No (Gemini) suffix
        self.assertIn("- Step 1: Check logs (Ollama)", plan)
        mock_llm.invoke.assert_called_once()

    def test_check_on_call_schedule_mock(self):
        """
        Verifies check_on_call_schedule returns the expected mock structure.
        """
        result = real.check_on_call_schedule.invoke({})
        self.assertIn("On-Call Schedule: Primary", result)
        self.assertIn("Current On-Call:", result)
        self.assertIn("Shift Ends:", result)
