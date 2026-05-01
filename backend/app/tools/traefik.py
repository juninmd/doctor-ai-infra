from langchain_core.tools import tool
import os
import requests
from typing import List, Dict, Optional
from kubernetes import client, config

def _get_traefik_api_url():
    """
    Tries to determine the Traefik API URL.
    In production, this usually points to the Traefik service in the cluster.
    """
    return os.getenv("TRAEFIK_API_URL", "http://traefik.kube-system.svc.cluster.local:8080")

@tool
def check_traefik_health() -> str:
    """
    Checks the health and version of the Traefik Ingress Controller.
    Queries the Traefik API /health or /api/overview if available.
    """
    api_url = _get_traefik_api_url()
    try:
        # 1. Try /health
        resp = requests.get(f"{api_url}/health", timeout=5)
        if resp.status_code == 200:
            return f"🟢 Traefik Health: OK (Status: {resp.status_code})"
        
        # 2. Try /api/overview (if dashboard enabled)
        resp = requests.get(f"{api_url}/api/overview", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            return f"🟢 Traefik Active. Providers: {len(data.get('providers', []))}, HTTP Services: {data.get('statistics', {}).get('http', {}).get('services', 0)}"
            
        return f"🟡 Traefik reachable but returned {resp.status_code} at {api_url}"
    except Exception as e:
        # Fallback: Check Kubernetes pod status for Traefik
        try:
            config.load_kube_config()
            v1 = client.CoreV1Api()
            pods = v1.list_pod_for_all_namespaces(label_selector="app.kubernetes.io/name=traefik")
            if not pods.items:
                pods = v1.list_pod_for_all_namespaces(label_selector="app=traefik")
            
            if pods.items:
                p = pods.items[0]
                return f"🟢 Traefik Pod '{p.metadata.name}' is {p.status.phase} in {p.metadata.namespace}. (API Unreachable: {e})"
            return f"🔴 Traefik pods not found in cluster. API also unreachable: {e}"
        except:
            return f"🔴 Traefik API unreachable: {e}"

@tool
def list_traefik_routes(namespace: str = "") -> str:
    """
    Lists HTTP routes managed by Traefik (IngressRoutes and standard Ingresses).
    """
    try:
        config.load_kube_config()
        custom_api = client.CustomObjectsApi()
        
        report = ["### 🛣️ Traefik Routing Table"]
        
        # 1. Custom IngressRoutes (Traefik CRD)
        try:
            routes = custom_api.list_cluster_custom_object(
                group="traefik.containo.us",
                version="v1alpha1",
                plural="ingressroutes"
            )
            for r in routes.get("items", []):
                ns = r['metadata']['namespace']
                if namespace and ns != namespace: continue
                name = r['metadata']['name']
                rule = r['spec'].get('routes', [{}])[0].get('kind', 'Rule')
                match = r['spec'].get('routes', [{}])[0].get('match', 'N/A')
                report.append(f"- [IngressRoute] {ns}/{name}: `{match}`")
        except:
             pass # CRD might not exist or permission denied

        # 2. Standard Ingresses
        v1_ing = client.NetworkingV1Api()
        ings = v1_ing.list_ingress_for_all_namespaces()
        for i in ings.items:
            ns = i.metadata.namespace
            if namespace and ns != namespace: continue
            name = i.metadata.name
            hosts = [h.host for h in i.spec.rules if h.host]
            report.append(f"- [Ingress] {ns}/{name}: {', '.join(hosts)}")

        if len(report) == 1:
            return "No Traefik routes found."
            
        return "\n".join(report)
    except Exception as e:
        return f"Error listing Traefik routes: {e}"

@tool
def diagnose_traefik_ingress(ingress_name: str, namespace: str = "default") -> str:
    """
    Diagnoses issues with a specific Traefik ingress/route.
    Checks: Backend service health, TLS secret status, and Middleware config.
    """
    try:
        config.load_kube_config()
        v1_net = client.NetworkingV1Api()
        v1_core = client.CoreV1Api()
        
        report = [f"### 🔍 Traefik Diagnosis: {namespace}/{ingress_name}"]
        
        # 1. Fetch Ingress
        try:
            ing = v1_net.read_namespaced_ingress(ingress_name, namespace)
        except:
            return f"Ingress '{ingress_name}' not found in namespace '{namespace}'."

        # 2. Check Backends
        for rule in ing.spec.rules:
            if rule.http:
                for path in rule.http.paths:
                    svc_name = path.backend.service.name
                    try:
                        svc = v1_core.read_namespaced_service(svc_name, namespace)
                        report.append(f"- Service '{svc_name}': 🟢 Found")
                        # Check endpoint health
                        ep = v1_core.read_namespaced_endpoints(svc_name, namespace)
                        if not ep.subsets:
                            report.append(f"  ⚠️ Warning: No endpoints found for service '{svc_name}' (Pod mismatch?).")
                        else:
                            ready = sum(len(s.addresses or []) for s in ep.subsets)
                            report.append(f"  🟢 {ready} healthy endpoints ready.")
                    except:
                        report.append(f"- Service '{svc_name}': 🔴 NOT FOUND")

        # 3. Check TLS
        if ing.spec.tls:
            for t in ing.spec.tls:
                secret_name = t.secret_name
                try:
                    v1_core.read_namespaced_secret(secret_name, namespace)
                    report.append(f"- TLS Secret '{secret_name}': 🟢 Found")
                except:
                    report.append(f"- TLS Secret '{secret_name}': 🔴 MISSING (SSL will fail)")

        return "\n".join(report)
    except Exception as e:
        return f"Traefik Diagnostic Error: {e}"
