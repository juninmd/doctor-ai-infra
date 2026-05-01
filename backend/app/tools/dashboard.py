from langchain_core.tools import tool
from .real import list_k8s_pods, check_gcp_status, get_active_alerts, get_cluster_events, query_gmp_prometheus
from .traefik import check_traefik_health

@tool
def analyze_infrastructure_health() -> str:
    """
    Performs a holistic health check across all infrastructure domains (K8s, GCP, Datadog, Traefik).
    Returns a dashboard-style Markdown report.
    """
    dashboard = ["# 🔍 Relatório de Integridade da Infraestrutura (2026)\n"]

    # 1. Kubernetes Check
    k8s_status = "✅ Operacional"
    k8s_details = ""
    try:
        # Check pods in default
        pods = list_k8s_pods.invoke({"namespace": "default"})
        # Check events
        events = get_cluster_events.invoke({"namespace": "default"})

        if "Error" in pods or "CrashLoopBackOff" in pods:
            k8s_status = "⚠️ Atenção Requerida"

        k8s_details = f"**Pods:** {pods[:100]}...\n**Eventos Recentes:**\n{events[:200]}..."
    except Exception as e:
        k8s_status = "❌ Erro de Conexão"
        k8s_details = str(e)

    dashboard.append(f"## ☸️ Kubernetes (Self-Hosted)\n**Status:** {k8s_status}\n\n<details><summary>Detalhes</summary>\n\n{k8s_details}\n</details>\n")

    # 2. GCP Check
    gcp_status = "✅ Operacional"
    gcp_details = ""
    try:
        gcp_res = check_gcp_status.invoke({})
        if "Error" in gcp_res:
             gcp_status = "⚠️ Falha na Verificação"

        # Add GMP Check
        try:
            # Simple query to check if metric collection is active
            gmp_res = query_gmp_prometheus.invoke({"query": "up"})
            gcp_details = f"{gcp_res}\n\n**GMP Metrics:**\n{gmp_res[:200]}..."
        except:
            gcp_details = f"{gcp_res}\n\n**GMP Metrics:** Indisponível."

    except Exception as e:
        gcp_status = "❌ Erro"
        gcp_details = str(e)

    dashboard.append(f"## ☁️ Google Cloud Platform (GCP)\n**Status:** {gcp_status}\n\n{gcp_details}\n")

    # 3. Datadog Alerts
    dd_status = "✅ Silencioso"
    dd_details = ""
    try:
        dd_res = get_active_alerts.invoke({})
        if "Alert" in dd_res and "No active alerts" not in dd_res:
            dd_status = "🔥 Alertas Ativos"
        dd_details = dd_res
    except Exception as e:
        dd_status = "❌ Erro"
        dd_details = str(e)

    dashboard.append(f"## 🐶 Datadog Observability\n**Status:** {dd_status}\n\n{dd_details}\n")

    # 4. Traefik Ingress
    traefik_status = "✅ Online"
    traefik_details = ""
    try:
        traefik_res = check_traefik_health.invoke({})
        if "🔴" in traefik_res:
            traefik_status = "❌ Erro"
        elif "🟡" in traefik_res:
            traefik_status = "⚠️ Atenção"
        traefik_details = traefik_res
    except Exception as e:
        traefik_status = "❌ Erro"
        traefik_details = str(e)

    dashboard.append(f"## 🚦 Traefik Ingress\n**Status:** {traefik_status}\n\n{traefik_details}\n")

    dashboard.append("\n---\n*Gerado automaticamente pelo Agente Supervisor 2026*")

    return "\n".join(dashboard)
