from langchain_core.tools import tool
import os
import requests
import json
from typing import List, Dict

# Infrastructure Libraries
try:
    from kubernetes import client, config
except ImportError:
    client = None
    config = None

try:
    from google.cloud import resourcemanager_v3, monitoring_v3
    from google.auth import default
    from google.auth.transport.requests import Request as GoogleAuthRequest
except ImportError:
    resourcemanager_v3 = None
    monitoring_v3 = None

try:
    from datadog_api_client import ApiClient, Configuration
    from datadog_api_client.v1.api.metrics_api import MetricsApi
    from datadog_api_client.v1.api.monitors_api import MonitorsApi
except ImportError:
    ApiClient = None

# --- Kubernetes Tools ---
def _get_k8s_client():
    if not config:
        raise ImportError("Kubernetes library not installed.")
    try:
        config.load_kube_config() # Try local config first
    except config.ConfigException:
        try:
            config.load_incluster_config() # Try inside pod
        except config.ConfigException:
            return None
    return client.CoreV1Api()

@tool
def list_k8s_pods(namespace: str = "default") -> str:
    """Lists all pods in the specified Kubernetes namespace."""
    v1 = _get_k8s_client()
    if not v1:
        return "Error: Could not load Kubernetes configuration. Check ~/.kube/config or service account."

    try:
        pods = v1.list_namespaced_pod(namespace)
        pod_list = []
        for pod in pods.items:
            pod_list.append(f"{pod.metadata.name} ({pod.status.phase})")

        if not pod_list:
            return f"No pods found in namespace {namespace}."

        return f"Pods in {namespace}: " + ", ".join(pod_list)
    except Exception as e:
        return f"Error listing pods: {str(e)}"

@tool
def describe_pod(pod_name: str, namespace: str = "default") -> str:
    """Describes a specific pod to get details about its status and events."""
    v1 = _get_k8s_client()
    if not v1:
        return "Error: Could not load Kubernetes configuration."

    try:
        pod = v1.read_namespaced_pod(name=pod_name, namespace=namespace)
        events = v1.list_namespaced_event(namespace, field_selector=f"involvedObject.name={pod_name}")

        event_msgs = [f"{e.type}: {e.message}" for e in events.items]

        info = [
            f"Name: {pod.metadata.name}",
            f"Status: {pod.status.phase}",
            f"IP: {pod.status.pod_ip}",
            f"Node: {pod.spec.node_name}",
            f"Events: {'; '.join(event_msgs) if event_msgs else 'None'}"
        ]
        return "\n".join(info)
    except Exception as e:
        return f"Error describing pod {pod_name}: {str(e)}"

@tool
def get_pod_logs(pod_name: str, namespace: str = "default", lines: int = 50) -> str:
    """Retrieves the last N lines of logs from a pod."""
    v1 = _get_k8s_client()
    if not v1:
        return "Error: Could not load Kubernetes configuration."

    try:
        logs = v1.read_namespaced_pod_log(name=pod_name, namespace=namespace, tail_lines=lines)
        return logs if logs else f"No logs found for pod {pod_name}."
    except Exception as e:
        return f"Error retrieving logs for {pod_name}: {str(e)}"

@tool
def get_cluster_events(namespace: str = "default") -> str:
    """Lists recent events in the cluster (or namespace) to identify systemic issues."""
    v1 = _get_k8s_client()
    if not v1:
        return "Error: Could not load Kubernetes configuration."

    try:
        events = v1.list_namespaced_event(namespace)
        event_list = []
        for e in events.items:
            # Format: [Warning] Pod/my-pod: Failed to pull image
            event_list.append(f"[{e.type}] {e.involved_object.kind}/{e.involved_object.name}: {e.message}")

        if not event_list:
             return f"No events found in namespace {namespace}."

        # Return last 20 events
        return "\n".join(event_list[-20:])
    except Exception as e:
        return f"Error listing events: {str(e)}"

# --- GCP Tools ---
@tool
def check_gcp_status(service: str = "compute") -> str:
    """Checks the status of Google Cloud Platform services via Resource Manager."""
    if not resourcemanager_v3:
        return "GCP libraries not installed."

    try:
        # Check if we can list projects
        rm_client = resourcemanager_v3.ProjectsClient()
        request = resourcemanager_v3.ListProjectsRequest()
        projects = rm_client.list_projects(request=request)

        project_list = [p.project_id for p in projects]
        return f"GCP Connection Successful. Active Projects: {', '.join(project_list[:5])}..."
    except Exception as e:
        return f"Error checking GCP status: {str(e)}. Check GOOGLE_APPLICATION_CREDENTIALS."

@tool
def query_gmp_prometheus(query: str) -> str:
    """Queries Google Managed Prometheus (GMP) for metrics."""
    if not monitoring_v3:
        return "GCP Monitoring library not installed."

    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        # Try to deduce from auth
        try:
            _, project_id = default()
        except Exception:
            pass

    if not project_id:
        return "Error: Could not determine Google Cloud Project ID. Set GOOGLE_CLOUD_PROJECT env var."

    try:
        client = monitoring_v3.QueryServiceClient()
        # Create request
        request = monitoring_v3.QueryTimeSeriesRequest(
            name=f"projects/{project_id}",
            query=query,
        )

        # Execute query
        # Note: GMP usually requires the Monitoring Query API to be enabled
        page_result = client.query_time_series(request=request)

        results = []
        for i, point in enumerate(page_result.time_series_data):
            if i > 5: break # Limit output
            # Extract basic value (assuming scalar or simple vector)
            val = "N/A"
            if point.point_data:
                 # Check value type (double, int, etc.)
                 pd = point.point_data[0]
                 val = pd.values[0].double_value or pd.values[0].int64_value

            label_desc = " ".join([f"{l.key}={l.value}" for l in point.label_values])
            results.append(f"Metric: {label_desc} | Value: {val}")

        if not results:
            return f"Query returned no data. Project: {project_id}, Query: {query}"

        return "\n".join(results)
    except Exception as e:
        return f"Error querying GMP: {str(e)}"

@tool
def list_compute_instances(zone: str = "us-central1-a") -> str:
    """Lists Google Cloud Compute Engine instances in a zone."""
    if not resourcemanager_v3:
        return "GCP libraries not installed."

    try:
        credentials, project = default()
        if not project:
            project = os.getenv("GOOGLE_CLOUD_PROJECT")

        if not project:
            return "Error: Could not determine GCP Project ID."

        # Refresh creds to get token
        credentials.refresh(GoogleAuthRequest())
        token = credentials.token

        headers = {"Authorization": f"Bearer {token}"}
        url = f"https://compute.googleapis.com/compute/v1/projects/{project}/zones/{zone}/instances"

        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()

        data = resp.json()
        instances = data.get("items", [])

        if not instances:
            return f"No instances found in {zone}."

        result = []
        for inst in instances:
            name = inst.get("name")
            status = inst.get("status")
            network_ip = inst.get("networkInterfaces", [{}])[0].get("networkIP", "N/A")
            result.append(f"{name} ({status}) - IP: {network_ip}")

        return "\n".join(result)

    except Exception as e:
        return f"Error listing compute instances: {str(e)}"

@tool
def get_gcp_sql_instances() -> str:
    """Lists Google Cloud SQL instances."""
    if not resourcemanager_v3:
        return "GCP libraries not installed."

    try:
        credentials, project = default()
        if not project:
            project = os.getenv("GOOGLE_CLOUD_PROJECT")

        credentials.refresh(GoogleAuthRequest())
        token = credentials.token

        headers = {"Authorization": f"Bearer {token}"}
        url = f"https://sqladmin.googleapis.com/sql/v1beta4/projects/{project}/instances"

        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()

        data = resp.json()
        instances = data.get("items", [])

        if not instances:
            return "No Cloud SQL instances found."

        result = []
        for inst in instances:
            name = inst.get("name")
            state = inst.get("state")
            db_version = inst.get("databaseVersion")
            result.append(f"{name} ({state}) - {db_version}")

        return "\n".join(result)

    except Exception as e:
        return f"Error listing SQL instances: {str(e)}"

# --- Datadog Tools ---
@tool
def get_datadog_metrics(query: str) -> str:
    """Queries Datadog for specific metrics."""
    if not ApiClient:
        return "Datadog library not installed."

    api_key = os.getenv("DD_API_KEY")
    app_key = os.getenv("DD_APP_KEY")

    if not api_key or not app_key:
        return "Error: DD_API_KEY and DD_APP_KEY environment variables must be set."

    configuration = Configuration()
    try:
        with ApiClient(configuration) as api_client:
            api_instance = MetricsApi(api_client)
            # Querying last 5 minutes
            import time
            current_time = int(time.time())
            response = api_instance.query_metrics(
                from_time=current_time - 300,
                to_time=current_time,
                query=query
            )
            return str(response)
    except Exception as e:
        return f"Error querying Datadog: {str(e)}"

@tool
def get_active_alerts(tags: str = "") -> str:
    """Gets active Datadog alerts (monitors in Alert state)."""
    if not ApiClient:
        return "Datadog library not installed."

    api_key = os.getenv("DD_API_KEY")
    app_key = os.getenv("DD_APP_KEY")

    if not api_key or not app_key:
        return "Error: DD_API_KEY and DD_APP_KEY must be set."

    configuration = Configuration()
    try:
        with ApiClient(configuration) as api_client:
            api_instance = MonitorsApi(api_client)
            # Search for triggered monitors
            query = "status:alert"
            if tags:
                query += f" tags:{tags}"

            # search_monitors returns metadata
            # list_monitors allows filtering
            response = api_instance.list_monitors(
                group_states="alert",
                tags=tags,
                page_size=5
            )

            alerts = []
            for monitor in response:
                alerts.append(f"[Alert] {monitor.name} (ID: {monitor.id}) - Status: {monitor.overall_state}")

            if not alerts:
                return "No active alerts found."

            return "\n".join(alerts)

    except Exception as e:
        return f"Error fetching Datadog alerts: {str(e)}"

# --- Azion Tools ---
@tool
def check_azion_edge(domain: str) -> str:
    """Checks the status of an Azion Edge Application via API."""
    token = os.getenv("AZION_TOKEN")
    if not token:
        return "Error: AZION_TOKEN environment variable is missing."

    headers = {
        "Accept": "application/json; version=3",
        "Authorization": f"Token {token}"
    }

    try:
        # Listing edge applications
        resp = requests.get("https://api.azionapi.net/edge_applications", headers=headers, timeout=10)
        resp.raise_for_status()
        apps = resp.json().get("results", [])

        target_app = next((a for a in apps if domain in a.get("name", "")), None)

        if target_app:
             return f"Azion App '{target_app['name']}' is Active. ID: {target_app['id']}."

        return f"Azion App for domain '{domain}' not found in first page of results."
    except Exception as e:
        return f"Error checking Azion: {str(e)}"

# --- DevOps / Git / Security Tools (Simplified wrappers) ---

@tool
def check_github_repos(org: str = "my-org") -> str:
    """Checks the status of GitHub repositories and recent commits."""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return "Error: GITHUB_TOKEN is missing."

    headers = {"Authorization": f"token {token}"}
    try:
        resp = requests.get(f"https://api.github.com/orgs/{org}/repos", headers=headers, timeout=10)
        if resp.status_code == 200:
            repos = resp.json()
            names = [r['name'] for r in repos[:5]]
            return f"Repositories in {org}: {', '.join(names)}"
        return f"GitHub API Error: {resp.status_code}"
    except Exception as e:
        return f"Error connecting to GitHub: {str(e)}"

@tool
def get_pr_status(pr_id: int) -> str:
    """Checks the status of a specific Pull Request."""
    # Simplified placeholder
    return f"Checking PR #{pr_id}... (Requires repo context)"

@tool
def check_pipeline_status(service: str) -> str:
    """Checks the status of CI/CD pipelines (GitHub Actions/Jenkins)."""
    return f"Checking pipeline for {service}... (Requires CI provider context)"

@tool
def get_argocd_sync_status(app_name: str) -> str:
    """Checks ArgoCD sync status."""
    # ArgoCD usually runs in K8s, could use K8s client to check Application CRD
    return f"Checking ArgoCD status for {app_name}... (Recommend using K8s_Specialist to check 'Application' CRD)"

@tool
def check_vulnerabilities(image: str) -> str:
    """Scans a container image for security vulnerabilities (Trivy/Snyk)."""
    return f"Triggering vulnerability scan for {image}... (Requires external scanner integration)"

@tool
def analyze_iam_policy(user: str) -> str:
    """Analyzes IAM policies for least privilege compliance."""
    return f"Analyzing IAM for {user}... (Requires cloud provider specific IAM tool)"

# --- Advanced SRE Tools (New) ---

@tool
def analyze_log_patterns(pod_name: str, namespace: str = "default") -> str:
    """
    Analyzes pod logs and returns a summary of error patterns.
    Useful for compressing large logs into actionable insights for the LLM.
    """
    # This tool calls another tool function logic directly, but get_pod_logs returns a string
    # We need to manually invoke the logic if we want raw access, but get_pod_logs is decorated
    # So we call it as a normal function (it returns a Tool object if accessed via .tool, but usually callable)
    # Langchain @tool decorated functions are callable.
    try:
        logs = get_pod_logs(pod_name, namespace, lines=200)
    except Exception:
        # Fallback if direct call fails (e.g. context issues), return simple msg
        return "Could not fetch logs for analysis."

    if "Error" in logs and "retrieving logs" in logs:
        return logs

    lines = logs.split('\n')
    error_counts = {}

    for line in lines:
        if "ERROR" in line or "Exception" in line or "Fail" in line:
            # Simple clustering: removing digits and timestamps might be complex,
            # so we just take the first 60 chars as the "signature"
            signature = line[:60]
            error_counts[signature] = error_counts.get(signature, 0) + 1

    if not error_counts:
        return "Log Analysis: No obvious ERROR/Exception patterns found in last 200 lines."

    summary = ["Log Analysis Summary:"]
    for sig, count in error_counts.items():
        summary.append(f"- Found {count} occurrences of: '{sig}...'")

    return "\n".join(summary)

@tool
def diagnose_service_health(service_name: str, namespace: str = "default") -> str:
    """
    Performs a comprehensive health check on a service.
    Orchestrates: Pod listing, Event checking, and Log analysis for failing pods.
    """
    report = [f"Health Diagnosis for '{service_name}' in '{namespace}':"]

    # 1. Check Pods
    try:
        pods_output = list_k8s_pods(namespace)
    except:
        pods_output = "Failed to list pods."
    report.append(f"\n1. Pod Status:\n{pods_output}")

    # 2. Check Events
    try:
        events_output = get_cluster_events(namespace)
    except:
        events_output = "Failed to list events."
    report.append(f"\n2. Recent Events:\n{events_output}")

    # 3. Analyze Logs if suspicious
    if service_name in pods_output:
        import re
        match = re.search(rf"({service_name}-[\w-]+)", pods_output)
        if match:
            pod_full_name = match.group(1)
            report.append(f"\n3. Log Analysis for {pod_full_name}:")
            try:
                logs_analysis = analyze_log_patterns(pod_full_name, namespace)
                report.append(logs_analysis)
            except:
                report.append("Failed to analyze logs.")

    return "\n".join(report)

@tool
def analyze_ci_failure(build_id: str, repo_name: str = "") -> str:
    """
    Analyzes a CI/CD build failure to pinpoint the cause.
    Fetches logs from GitHub Actions (if token available) or mock.
    """
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return "Error: GITHUB_TOKEN not set. Cannot fetch CI logs."

    return f"Analysis: Build {build_id} failed. (Real log fetching implementation pending integration with specific repo context)."

@tool
def create_issue(title: str, description: str, project: str = "SRE", severity: str = "Medium", system: str = "Jira") -> str:
    """
    Creates an issue/ticket in an external tracking system (Jira or GitHub).
    """
    if system.lower() == "jira":
        jira_url = os.getenv("JIRA_URL")
        jira_user = os.getenv("JIRA_USER")
        jira_token = os.getenv("JIRA_API_TOKEN")

        if not (jira_url and jira_user and jira_token):
             return "Error: JIRA_URL, JIRA_USER, and JIRA_API_TOKEN must be set."

        payload = {
            "fields": {
                "project": {"key": project},
                "summary": title,
                "description": description,
                "issuetype": {"name": "Task"}
            }
        }
        try:
            resp = requests.post(
                f"{jira_url}/rest/api/2/issue",
                json=payload,
                auth=(jira_user, jira_token),
                headers={"Content-Type": "application/json"}
            )
            resp.raise_for_status()
            key = resp.json().get("key")
            return f"Jira Issue created: {key} ({jira_url}/browse/{key})"
        except Exception as e:
            return f"Failed to create Jira issue: {str(e)}"

    elif system.lower() == "github":
        return f"GitHub Issue creation pending implementation. Use 'check_github_repos' for status."

    return f"Unknown system '{system}'. Supported: Jira, GitHub."
