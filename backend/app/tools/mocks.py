from langchain_core.tools import tool
from typing import List, Dict

@tool
def list_k8s_pods(namespace: str = "default") -> str:
    """Lists all pods in the specified Kubernetes namespace."""
    # Mock implementation
    if namespace == "default":
        # Simulate a crashing frontend pod
        return "Pods in default: [frontend-7d6f (CrashLoopBackOff), backend-9s8d (Running), db-postgres-1a2b (Running)]"
    elif namespace == "kube-system":
        return "Pods in kube-system: [coredns-1, coredns-2, kube-proxy-x, etcd-0]"
    return f"No pods found in namespace {namespace}."

@tool
def describe_pod(pod_name: str, namespace: str = "default") -> str:
    """Describes a specific pod to get details about its status and events."""
    # Mock implementation
    if "backend" in pod_name:
        return f"Name: {pod_name}\nStatus: Running\nRestarts: 0\nEvents: Pulled image successfully."
    elif "frontend" in pod_name:
        # Simulate a database connection error in the logs
        return (
            f"Name: {pod_name}\n"
            "Status: CrashLoopBackOff\n"
            "Restarts: 5\n"
            "Events: Back-off restarting failed container\n"
            "Logs:\n"
            "[INFO] Starting server...\n"
            "[ERROR] ConnectionRefusedError: POST https://postgres-db:5432 - Connection refused\n"
            "[FATAL] Unable to connect to database. Exiting.\n"
            "Caused by: ConnectionRefusedError: POST https://postgres-db:5432 - Connection refused"
        )
    return f"Pod {pod_name} not found."

@tool
def check_gcp_status(service: str = "compute") -> str:
    """Checks the status of Google Cloud Platform services."""
    # Simulate maintenance mode for Cloud SQL
    if "sql" in service.lower() or "db" in service.lower() or "postgres" in service.lower():
        return "GCP Service Cloud SQL (postgres-db) is in MAINTENANCE mode. Scheduled update in progress."
    return f"GCP Service {service} is OPERATIONAL. No incidents reported."

@tool
def query_gmp_prometheus(query: str) -> str:
    """Queries Google Managed Prometheus (GMP) for metrics."""
    return f"GMP Query '{query}' returned: cpu_usage=0.45"

@tool
def get_datadog_metrics(query: str) -> str:
    """Queries Datadog for specific metrics."""
    return f"Datadog Metric for '{query}': Avg 45ms latency, 99.9% availability."

@tool
def check_azion_edge(domain: str) -> str:
    """Checks the status of an Azion Edge Application."""
    return f"Azion Edge for {domain}: Cache Hit Ratio 85%, Status Active."

# --- NEW TOOLS FOR 2026 DEVOPS AGENTS ---

@tool
def check_github_repos(org: str = "my-org") -> str:
    """Checks the status of GitHub repositories and recent commits."""
    return f"GitHub Org {org}: 5 active repos. Latest commit on 'frontend-repo': 'fix: typo in header' by dev-alex."

@tool
def get_pr_status(pr_id: int) -> str:
    """Checks the status of a specific Pull Request."""
    return f"PR #{pr_id}: Open. CI checks pending. 2 approvals."

@tool
def check_pipeline_status(service: str) -> str:
    """Checks the status of CI/CD pipelines (GitHub Actions/Jenkins)."""
    if "frontend" in service:
        return f"Pipeline for {service}: FAILED. Step 'Build Docker Image' failed. Error: 'npm run build' exited with code 1."
    return f"Pipeline for {service}: SUCCEEDED. Deployed to staging 5m ago."

@tool
def get_argocd_sync_status(app_name: str) -> str:
    """Checks ArgoCD sync status."""
    return f"ArgoCD App '{app_name}': Synced. Health: Healthy."

@tool
def check_vulnerabilities(image: str) -> str:
    """Scans a container image for security vulnerabilities (Trivy/Snyk)."""
    if "frontend" in image:
        return f"Scan for {image}: 2 CRITICAL, 5 HIGH vulnerabilities found. CVE-2026-1234 (Node.js)."
    return f"Scan for {image}: Passed. No critical vulnerabilities."

@tool
def analyze_iam_policy(user: str) -> str:
    """Analyzes IAM policies for least privilege compliance."""
    return f"IAM Analysis for {user}: Warning. User has 'Owner' permission on project. Recommend downgrading to 'Editor'."
