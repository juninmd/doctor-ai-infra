import pytest
from unittest.mock import patch
from app.tools.dashboard import analyze_infrastructure_health

def test_analyze_infrastructure_health_success():
    """
    Test when all integrations (k8s, GCP, Datadog, Traefik) return healthy status.
    """
    with patch("app.tools.dashboard.list_k8s_pods") as mock_k8s, \
         patch("app.tools.dashboard.get_cluster_events") as mock_events, \
         patch("app.tools.dashboard.check_gcp_status") as mock_gcp, \
         patch("app.tools.dashboard.query_gmp_prometheus") as mock_gmp, \
         patch("app.tools.dashboard.get_active_alerts") as mock_alerts, \
         patch("app.tools.dashboard.check_traefik_health") as mock_traefik:

        mock_k8s.invoke.return_value = "pod1, pod2"
        mock_events.invoke.return_value = "event1"
        mock_gcp.invoke.return_value = "All systems operational"
        mock_gmp.invoke.return_value = "up == 1"
        mock_alerts.invoke.return_value = "No active alerts"
        mock_traefik.invoke.return_value = "🟢 Traefik: Active"

        result = analyze_infrastructure_health.invoke({})

        assert "## ☸️ Kubernetes (Self-Hosted)" in result
        assert "✅ Operacional" in result

        assert "## ☁️ Google Cloud Platform (GCP)" in result
        assert "✅ Operacional" in result

        assert "## 🐶 Datadog Observability" in result
        assert "✅ Silencioso" in result

        assert "## 🚦 Traefik Ingress" in result
        assert "✅ Online" in result

def test_analyze_infrastructure_health_failure():
    """
    Test when integrations return errors or warnings.
    """
    with patch("app.tools.dashboard.list_k8s_pods") as mock_k8s, \
         patch("app.tools.dashboard.get_cluster_events") as mock_events, \
         patch("app.tools.dashboard.check_gcp_status") as mock_gcp, \
         patch("app.tools.dashboard.query_gmp_prometheus") as mock_gmp, \
         patch("app.tools.dashboard.get_active_alerts") as mock_alerts, \
         patch("app.tools.dashboard.check_traefik_health") as mock_traefik:

        mock_k8s.invoke.return_value = "CrashLoopBackOff"
        mock_events.invoke.return_value = "Error syncing"
        mock_gcp.invoke.return_value = "Error: API down"
        mock_gmp.invoke.side_effect = Exception("Failed")
        mock_alerts.invoke.return_value = "Alert: High latency"
        mock_traefik.invoke.return_value = "🔴 Error"

        result = analyze_infrastructure_health.invoke({})

        assert "## ☸️ Kubernetes (Self-Hosted)" in result
        assert "⚠️ Atenção Requerida" in result

        assert "## ☁️ Google Cloud Platform (GCP)" in result
        assert "⚠️ Falha na Verificação" in result
        assert "Indisponível." in result

        assert "## 🐶 Datadog Observability" in result
        assert "🔥 Alertas Ativos" in result

        assert "## 🚦 Traefik Ingress" in result
        assert "❌ Erro" in result

def test_analyze_infrastructure_health_exception():
    """
    Test when integrations throw raw exceptions instead of returning error strings.
    """
    with patch("app.tools.dashboard.list_k8s_pods") as mock_k8s, \
         patch("app.tools.dashboard.check_gcp_status") as mock_gcp, \
         patch("app.tools.dashboard.get_active_alerts") as mock_alerts, \
         patch("app.tools.dashboard.check_traefik_health") as mock_traefik:

        mock_k8s.invoke.side_effect = Exception("Timeout")
        mock_gcp.invoke.side_effect = Exception("Timeout")
        mock_alerts.invoke.side_effect = Exception("Timeout")
        mock_traefik.invoke.side_effect = Exception("Timeout")

        result = analyze_infrastructure_health.invoke({})

        assert "## ☸️ Kubernetes (Self-Hosted)" in result
        assert "❌ Erro de Conexão" in result

        assert "## ☁️ Google Cloud Platform (GCP)" in result
        assert "❌ Erro" in result

        assert "## 🐶 Datadog Observability" in result
        assert "❌ Erro" in result

        assert "## 🚦 Traefik Ingress" in result
        assert "❌ Erro" in result
