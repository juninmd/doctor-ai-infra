import pytest
from unittest.mock import patch
from app.tools.dashboard import analyze_infrastructure_health

def test_analyze_infrastructure_health_success():
    """
    Test when all integrations (k8s, GCP, Datadog, Azion) return healthy status.
    """
    with patch("app.tools.dashboard.list_k8s_pods._run", return_value="pod1, pod2"), \
         patch("app.tools.dashboard.get_cluster_events._run", return_value="event1"), \
         patch("app.tools.dashboard.check_gcp_status._run", return_value="All systems operational"), \
         patch("app.tools.dashboard.query_gmp_prometheus._run", return_value="up == 1"), \
         patch("app.tools.dashboard.get_active_alerts._run", return_value="No active alerts"), \
         patch("app.tools.dashboard.diagnose_azion_configuration._run", return_value="Edge is ONLINE"):

        result = analyze_infrastructure_health.invoke({})

        assert "## ☸️ Kubernetes (Self-Hosted)" in result
        assert "✅ Operacional" in result

        assert "## ☁️ Google Cloud Platform (GCP)" in result
        assert "✅ Operacional" in result

        assert "## 🐶 Datadog Observability" in result
        assert "✅ Silencioso" in result

        assert "## ⚡ Azion Edge" in result
        assert "✅ Online" in result

def test_analyze_infrastructure_health_failure():
    """
    Test when integrations return errors or warnings.
    """
    with patch("app.tools.dashboard.list_k8s_pods._run", return_value="CrashLoopBackOff"), \
         patch("app.tools.dashboard.get_cluster_events._run", return_value="Error syncing"), \
         patch("app.tools.dashboard.check_gcp_status._run", return_value="Error: API down"), \
         patch("app.tools.dashboard.query_gmp_prometheus._run", side_effect=Exception("Failed")), \
         patch("app.tools.dashboard.get_active_alerts._run", return_value="Alert: High latency"), \
         patch("app.tools.dashboard.diagnose_azion_configuration._run", return_value="OFFLINE"):

        result = analyze_infrastructure_health.invoke({})

        assert "## ☸️ Kubernetes (Self-Hosted)" in result
        assert "⚠️ Atenção Requerida" in result

        assert "## ☁️ Google Cloud Platform (GCP)" in result
        assert "⚠️ Falha na Verificação" in result
        assert "Indisponível." in result

        assert "## 🐶 Datadog Observability" in result
        assert "🔥 Alertas Ativos" in result

        assert "## ⚡ Azion Edge" in result
        assert "⚠️ Atenção" in result

def test_analyze_infrastructure_health_exception():
    """
    Test when integrations throw raw exceptions instead of returning error strings.
    """
    with patch("app.tools.dashboard.list_k8s_pods._run", side_effect=Exception("Timeout")), \
         patch("app.tools.dashboard.check_gcp_status._run", side_effect=Exception("Timeout")), \
         patch("app.tools.dashboard.get_active_alerts._run", side_effect=Exception("Timeout")), \
         patch("app.tools.dashboard.diagnose_azion_configuration._run", side_effect=Exception("Timeout")):

        result = analyze_infrastructure_health.invoke({})

        assert "## ☸️ Kubernetes (Self-Hosted)" in result
        assert "❌ Erro de Conexão" in result

        assert "## ☁️ Google Cloud Platform (GCP)" in result
        assert "❌ Erro" in result

        assert "## 🐶 Datadog Observability" in result
        assert "❌ Erro" in result

        assert "## ⚡ Azion Edge" in result
        assert "❌ Erro" in result
