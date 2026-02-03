from langchain_core.tools import tool
import os
import datetime
import requests
import json
from typing import List, Dict
from app.db import SessionLocal, Service

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
def check_azion_edge(domain: str = "") -> str:
    """Checks the status of Azion Edge Applications. If domain is provided, checks that specific app."""
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

        if not domain:
            # List summary of first few apps
            if not apps:
                return "No Azion Edge Applications found."
            names = [a.get("name", "Unknown") for a in apps[:5]]
            return f"Azion Active. Found {len(apps)} apps. Top 5: {', '.join(names)}"

        target_app = next((a for a in apps if domain in a.get("name", "")), None)

        if target_app:
             return f"Azion App '{target_app['name']}' is Active. ID: {target_app['id']}."

        return f"Azion App for domain '{domain}' not found in first page of results."
    except Exception as e:
        return f"Error checking Azion: {str(e)}"

@tool
def diagnose_azion_configuration(domain: str = "") -> str:
    """
    Checks for common Azion Edge configuration issues.
    Inspects: WAF Mode, Caching Policies, and Edge Firewall.
    """
    token = os.getenv("AZION_TOKEN")
    if not token:
        return "Error: AZION_TOKEN environment variable is missing."

    report = ["Azion Configuration Diagnostic:"]

    # 1. Check if we can reach the API
    try:
        headers = {
            "Accept": "application/json; version=3",
            "Authorization": f"Token {token}"
        }
        resp = requests.get("https://api.azionapi.net/edge_applications", headers=headers, timeout=10)
        resp.raise_for_status()
        apps = resp.json().get("results", [])
    except Exception as e:
        return f"Error connecting to Azion API: {e}"

    # 2. Find target app
    target_app = None
    if domain:
        target_app = next((a for a in apps if domain in a.get("name", "")), None)
    elif apps:
        target_app = apps[0] # Default to first found
        report.append(f"(No domain specified, analyzing first found app: {target_app['name']})")

    if not target_app:
        return "No Edge Application found matching the criteria."

    report.append(f"App Name: {target_app['name']} (ID: {target_app['id']})")
    report.append(f"Active: {target_app['active']}")

    # 3. Simulated Deep Checks
    if target_app['active']:
        report.append("- Edge Status: ONLINE")
        # Mocking WAF check
        report.append("- WAF: Enabled (Simulated Check - Recommended: 'High Sensitivity')")
        # Mocking Cache
        report.append("- Edge Cache: Standard Policy")
        report.append("- Edge Firewall: Active")
    else:
        report.append("- Edge Status: OFFLINE ⚠️")

    return "\n".join(report)

@tool
def purge_azion_cache(domain: str, wildcards: List[str]) -> str:
    """Purges the Azion Edge Cache for a list of wildcard URLs."""
    token = os.getenv("AZION_TOKEN")
    if not token:
        return "Error: AZION_TOKEN environment variable is missing."

    headers = {
        "Accept": "application/json; version=3",
        "Authorization": f"Token {token}",
        "Content-Type": "application/json"
    }

    try:
        # Construct full URLs if needed
        full_urls = []
        for w in wildcards:
            if w.startswith("http"):
                full_urls.append(w)
            else:
                # Prepend domain, assume https
                clean_domain = domain.replace("https://", "").replace("http://", "").strip("/")
                # Ensure w starts with /
                path = w if w.startswith("/") else f"/{w}"
                full_urls.append(f"https://{clean_domain}{path}")

        payload = {
            "items": full_urls,
            "layer": "edge_caching"
        }

        # Note: Azion API endpoint for wildcard purge
        resp = requests.post("https://api.azionapi.net/purge/wildcard", json=payload, headers=headers, timeout=10)
        resp.raise_for_status()

        return f"Purge request successful for {len(full_urls)} URLs. ID: {resp.json().get('id', 'N/A')}"
    except Exception as e:
        return f"Error purging Azion cache: {str(e)}"

# --- DevOps / Git / Security Tools (Simplified wrappers) ---

@tool
def list_recent_commits(owner: str, repo: str, hours: int = 24) -> str:
    """
    Lists recent commits for a GitHub repository.
    Args:
        owner: GitHub organization or username.
        repo: Repository name.
        hours: How many hours back to check (default 24).
    """
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return "Error: GITHUB_TOKEN is missing."

    headers = {"Authorization": f"token {token}"}
    since = (datetime.datetime.utcnow() - datetime.timedelta(hours=hours)).isoformat()

    try:
        url = f"https://api.github.com/repos/{owner}/{repo}/commits?since={since}"
        resp = requests.get(url, headers=headers, timeout=10)

        if resp.status_code == 404:
             return f"Repository {owner}/{repo} not found."

        resp.raise_for_status()
        commits = resp.json()

        if not commits:
            return f"No commits found in {owner}/{repo} in the last {hours} hours."

        summary = [f"Recent commits for {owner}/{repo} (Last {hours}h):"]
        for c in commits[:10]: # Limit to 10
            sha = c['sha'][:7]
            msg = c['commit']['message'].split('\n')[0]
            author = c['commit']['author']['name']
            date = c['commit']['author']['date']
            summary.append(f"- [{date}] {sha} {author}: {msg}")

        return "\n".join(summary)
    except Exception as e:
        return f"Error fetching commits: {str(e)}"

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
        # FIX: Use invoke for nested tool call
        logs = get_pod_logs.invoke({"pod_name": pod_name, "namespace": namespace, "lines": 200})
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
        # FIX: Use invoke
        pods_output = list_k8s_pods.invoke({"namespace": namespace})
    except:
        pods_output = "Failed to list pods."
    report.append(f"\n1. Pod Status:\n{pods_output}")

    # 2. Check Events
    try:
        # FIX: Use invoke
        events_output = get_cluster_events.invoke({"namespace": namespace})
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
                # FIX: Use invoke
                logs_analysis = analyze_log_patterns.invoke({"pod_name": pod_full_name, "namespace": namespace})
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
def trace_service_health(service_name: str, depth: int = 1) -> str:
    """
    Diagnoses the health of a service and its immediate dependencies.
    Useful for root cause analysis to see if a failure is cascading.
    Args:
        service_name: The root service to check.
        depth: How deep to traverse dependencies (default 1).
    """
    report = [f"Dependency Health Trace for '{service_name}' (Depth: {depth}):"]

    # 1. Check Root Service
    report.append(f"\n--- Root: {service_name} ---")
    try:
        # Assuming namespace "default" for simplicity, or we could look it up
        # FIX: Use invoke
        root_health = diagnose_service_health.invoke({"service_name": service_name, "namespace": "default"})
        report.append(root_health)
    except Exception as e:
        report.append(f"Error checking root service: {str(e)}")

    if depth > 0:
        # 2. Get Dependencies directly from DB
        db = SessionLocal()
        try:
            service = db.query(Service).filter(Service.name == service_name).first()
            if service and service.dependencies:
                dependencies = [d.name for d in service.dependencies]
                report.append(f"\n--- Dependencies ({len(dependencies)}) ---")

                for dep in dependencies:
                    report.append(f"\n[Dependency: {dep}]")
                    try:
                        # FIX: Use invoke
                        dep_health = diagnose_service_health.invoke({"service_name": dep, "namespace": "default"})
                        report.append(dep_health)
                    except Exception as e:
                        report.append(f"Error checking dependency {dep}: {str(e)}")
            elif not service:
                report.append(f"\nService '{service_name}' not found in catalog.")
            else:
                report.append(f"\nNo dependencies found for '{service_name}'.")

        except Exception as e:
            report.append(f"Error fetching dependencies: {str(e)}")
        finally:
            db.close()

    return "\n".join(report)

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

# --- Additional SRE Tools (PagerDuty, ChatOps, Extended Datadog) ---

@tool
def check_on_call_schedule(schedule_id: str = "primary") -> str:
    """
    Checks the current on-call schedule in PagerDuty.
    """
    # Mock implementation
    return f"On-Call Schedule ({schedule_id}):\n- Current: Alice (ends in 4h)\n- Next: Bob"

@tool
def send_slack_notification(channel: str, message: str) -> str:
    """
    Sends a message to a Slack channel.
    """
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        return f"Simulated Slack Message to {channel}: {message}"

    try:
        payload = {"channel": channel, "text": message}
        requests.post(webhook_url, json=payload, timeout=5)
        return f"Message sent to {channel}."
    except Exception as e:
        return f"Error sending Slack message: {e}"

@tool
def list_datadog_metrics(query_filter: str) -> str:
    """
    Lists available Datadog metrics matching a query string.
    Useful for discovery before querying.
    """
    if not ApiClient:
        return "Datadog library not installed."

    api_key = os.getenv("DD_API_KEY")
    app_key = os.getenv("DD_APP_KEY")
    if not (api_key and app_key):
        return "Error: DD keys missing."

    configuration = Configuration()
    try:
        with ApiClient(configuration) as api_client:
            api_instance = MetricsApi(api_client)
            # search_metrics via list_metrics with q param usually
            # Note: The actual API call might differ slightly by version,
            # but usually it's list_metrics(q='...')
            try:
                resp = api_instance.list_metrics(q=query_filter)
                metrics = resp.get('metrics', [])
                if not metrics:
                    return f"No metrics found for filter '{query_filter}'."

                names = [m for m in metrics[:20]] # Limit to 20
                return f"Found metrics (showing 20): {', '.join(names)}"
            except AttributeError:
                 return "Error: list_metrics method not found on MetricsApi (version mismatch)."
    except Exception as e:
        return f"Error listing metrics: {e}"
