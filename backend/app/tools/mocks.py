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
def get_pod_logs(pod_name: str, namespace: str = "default", lines: int = 50) -> str:
    """Retrieves the last N lines of logs from a pod."""
    if "frontend" in pod_name:
         return (
             "[INFO] Application starting...\n"
             "[INFO] Connected to Redis cache\n"
             "[ERROR] ConnectionRefusedError: POST https://postgres-db:5432 - Connection refused\n"
             "[FATAL] Database connection failed after 3 retries.\n"
             "Process exited with code 1"
         )
    elif "backend" in pod_name:
         return (
             "[INFO] Worker process started\n"
             "[INFO] Processing job #1023\n"
             "[INFO] Job #1023 completed successfully"
         )
    return f"Logs for {pod_name} (mock):\n[INFO] Service running normally."

@tool
def get_cluster_events(namespace: str = "default") -> str:
    """Lists recent events in the cluster (or namespace) to identify systemic issues."""
    return (
        "[Normal] Pod/backend-9s8d: Scheduled\n"
        "[Normal] Pod/backend-9s8d: Pulled image 'backend:v2'\n"
        "[Warning] Pod/frontend-7d6f: Failed to pull image 'frontend:v3.1' (image not found)\n"
        "[Warning] Pod/frontend-7d6f: Back-off restarting failed container"
    )

@tool
def check_gcp_status(service: str = "compute") -> str:
    """Checks the status of Google Cloud Platform services."""
    # Simulate maintenance mode for Cloud SQL
    if "sql" in service.lower() or "db" in service.lower() or "postgres" in service.lower():
        return "GCP Service Cloud SQL (postgres-db) is in MAINTENANCE mode. Scheduled update in progress."
    return f"GCP Service {service} is OPERATIONAL. No incidents reported."

@tool
def list_compute_instances(zone: str = "us-central1-a") -> str:
    """Lists Google Cloud Compute Engine instances in a zone."""
    return (
        "web-server-1 (RUNNING) - IP: 10.0.0.4\n"
        "worker-node-1 (RUNNING) - IP: 10.0.0.5\n"
        "worker-node-2 (RUNNING) - IP: 10.0.0.6"
    )

@tool
def get_gcp_sql_instances() -> str:
    """Lists Google Cloud SQL instances."""
    return "postgres-db (MAINTENANCE) - POSTGRES_15"

@tool
def query_gmp_prometheus(query: str) -> str:
    """Queries Google Managed Prometheus (GMP) for metrics."""
    return f"GMP Query '{query}' returned: cpu_usage=0.45"

@tool
def get_datadog_metrics(query: str) -> str:
    """Queries Datadog for specific metrics."""
    return f"Datadog Metric for '{query}': Avg 45ms latency, 99.9% availability."

@tool
def get_active_alerts(tags: str = "") -> str:
    """Gets active Datadog alerts (monitors in Alert state)."""
    if "payment" in tags or not tags:
        return "[Alert] Payment API High Latency (ID: 12345) - Status: Alert"
    return "No active alerts found."

@tool
def check_azion_edge(domain: str) -> str:
    """Checks the status of an Azion Edge Application."""
    return f"Azion Edge for {domain}: Cache Hit Ratio 85%, Status Active."

@tool
def purge_azion_cache(domain: str, wildcards: List[str]) -> str:
    """Purges the Azion Edge Cache for a list of wildcard URLs (Mock)."""
    # Simulate URL construction logic
    full_urls = []
    for w in wildcards:
        if w.startswith("http"):
            full_urls.append(w)
        else:
            clean_domain = domain.replace("https://", "").replace("http://", "").strip("/")
            path = w if w.startswith("/") else f"/{w}"
            full_urls.append(f"https://{clean_domain}{path}")

    return f"Purge request for {domain} (URLs: {full_urls}) created successfully. Mock ID: 998877."

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

# --- Advanced SRE Tools (New - Mocks) ---

@tool
def analyze_log_patterns(pod_name: str, namespace: str = "default") -> str:
    """
    Analyzes pod logs and returns a summary of error patterns (Mock).
    """
    if "frontend" in pod_name:
        return (
            "Log Analysis Summary:\n"
            "- Found 15 occurrences of: '[ERROR] ConnectionRefusedError: POST https://postgres-db:5432...'\n"
            "- Found 3 occurrences of: '[FATAL] Database connection failed...'\n"
            "Recommendation: Check 'postgres-db' service."
        )
    return "Log Analysis: No significant error patterns found."

@tool
def diagnose_service_health(service_name: str, namespace: str = "default") -> str:
    """
    Performs a comprehensive health check on a service (Mock).
    """
    if "frontend" in service_name:
        return (
            f"Health Diagnosis for '{service_name}' in '{namespace}':\n"
            "\n1. Pod Status:\nfrontend-7d6f (CrashLoopBackOff)\n"
            "\n2. Recent Events:\n[Warning] Pod/frontend-7d6f: Back-off restarting failed container\n"
            "\n3. Log Analysis for frontend-7d6f:\n"
            "- Found 15 occurrences of: '[ERROR] ConnectionRefusedError: POST https://postgres-db:5432...'\n"
            "Summary: Service is crashing due to Database Connection Errors."
        )
    return f"Health Diagnosis for '{service_name}': All Systems Operational. Pods Running. No Alerts."

@tool
def analyze_ci_failure(build_id: str, repo_name: str = "") -> str:
    """
    Analyzes a CI/CD build failure (Mock).
    """
    return (
        f"Analysis: Build {build_id} failed.\n"
        "Reason: Test Failure in 'tests/unit/test_auth.py'.\n"
        "Error: 'AssertionError: Expected 200 OK, got 500 Internal Server Error'\n"
        "Commit Author: dev-alex"
    )

@tool
def trace_service_health(service_name: str, depth: int = 1) -> str:
    """
    Diagnoses the health of a service and its immediate dependencies.
    Useful for root cause analysis to see if a failure is cascading.
    (Mock Implementation)
    """
    report = [f"Dependency Health Trace for '{service_name}' (Depth: {depth}):"]

    # 1. Check Root
    report.append(f"\n--- Root: {service_name} ---")
    if "frontend" in service_name:
        report.append(diagnose_service_health.invoke({"service_name": service_name}))
        if depth > 0:
            report.append("\n--- Dependencies (2) ---")
            report.append("\n[Dependency: payment-api]")
            report.append(diagnose_service_health.invoke({"service_name": "payment-api"}))
            report.append("\n[Dependency: product-api]")
            report.append(diagnose_service_health.invoke({"service_name": "product-api"}))
    else:
        report.append(diagnose_service_health.invoke({"service_name": service_name}))

    return "\n".join(report)

@tool
def create_issue(title: str, description: str, project: str = "SRE", severity: str = "Medium", system: str = "Jira") -> str:
    """
    Creates an issue/ticket (Mock).
    """
    import random
    fake_id = f"{project}-{random.randint(1000, 9999)}"
    return f"[{system} Mock] Issue created successfully. Key: {fake_id}. (Title: {title})"
