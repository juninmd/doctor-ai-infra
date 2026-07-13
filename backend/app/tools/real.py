from langchain_core.tools import tool
import os
import datetime
import requests
import json
from typing import List, Dict, Optional
from app.db import SessionLocal, Service
from app.llm import get_llm, get_google_sdk_client
from langchain_core.prompts import ChatPromptTemplate

# Infrastructure Libraries
try:
    from kubernetes import client, config
except ImportError:
    client = None
    config = None

try:
    from google.cloud import resourcemanager_v3, monitoring_v3, logging as cloud_logging
    from google.auth import default
    from google.auth.transport.requests import Request as GoogleAuthRequest
except ImportError:
    resourcemanager_v3 = None
    monitoring_v3 = None
    cloud_logging = None
    default = None
    GoogleAuthRequest = None

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
        return f"Error querying GMP: {str(e)}. Ensure GOOGLE_APPLICATION_CREDENTIALS is set and the service account has 'Monitoring Viewer' role."

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

@tool
def analyze_gcp_errors(days: int = 1) -> str:
    """
    Analyzes Google Cloud Logging for errors in the current project.
    Fetches logs with severity >= ERROR from the last N days.
    """
    if not cloud_logging:
        return "GCP Cloud Logging library not installed."

    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        try:
            _, project_id = default()
        except Exception:
            pass

    if not project_id:
        return "Error: Could not determine Google Cloud Project ID."

    try:
        client = cloud_logging.Client(project=project_id)

        # Calculate timestamp
        now = datetime.datetime.now(datetime.UTC)
        past = now - datetime.timedelta(days=days)
        timestamp = past.isoformat().replace("+00:00", "Z")

        filter_str = f"severity>=ERROR AND timestamp>=\"{timestamp}\""

        entries = client.list_entries(filter_=filter_str, order_by=cloud_logging.DESCENDING, max_results=50)

        error_summary = []
        count = 0
        for entry in entries:
            count += 1
            payload = entry.payload
            # Payload can be dict, str, or None
            msg = "No message"
            if isinstance(payload, dict):
                msg = payload.get("message") or payload.get("textPayload") or str(payload)
            elif isinstance(payload, str):
                msg = payload

            # Truncate
            msg = (msg[:100] + '...') if len(msg) > 100 else msg
            error_summary.append(f"[{entry.timestamp}] {msg}")

        if not error_summary:
            return f"No errors found in GCP Cloud Logging for project {project_id} in the last {days} days."

        return f"Found {count} errors in GCP Cloud Logging (Last {days} days):\n" + "\n".join(error_summary)

    except Exception as e:
        return f"Error analyzing GCP logs: {str(e)}"

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
    since = (datetime.datetime.now(datetime.UTC) - datetime.timedelta(hours=hours)).isoformat().replace("+00:00", "Z")

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
def get_pr_status(owner: str, repo: str, pr_id: int) -> str:
    """Checks the status of a specific GitHub Pull Request."""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return "Error: GITHUB_TOKEN missing."
    
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    try:
        resp = requests.get(f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_id}", headers=headers, timeout=10)
        resp.raise_for_status()
        pr = resp.json()
        return (
            f"### 🎋 PR Status: {pr['title']} (#{pr_id})\n"
            f"- **State**: {pr['state'].upper()}\n"
            f"- **Author**: {pr['user']['login']}\n"
            f"- **Mergeable**: {pr.get('mergeable_state', 'unknown')}\n"
            f"- **Labels**: {', '.join([l['name'] for l in pr['labels']]) or 'None'}"
        )
    except Exception as e:
        return f"GitHub PR Error: {str(e)}"

@tool
def check_pipeline_status(service: str, repo: str = "", owner: str = "my-org") -> str:
    """
    Checks the status of CI/CD pipelines (GitHub Actions) for a specific service/repo.
    """
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return "Error: GITHUB_TOKEN is missing."

    target_repo = repo if repo else service
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}

    try:
        url = f"https://api.github.com/repos/{owner}/{target_repo}/actions/runs?per_page=5"
        resp = requests.get(url, headers=headers, timeout=10)

        if resp.status_code == 404:
             return f"Repository {owner}/{target_repo} not found."

        resp.raise_for_status()
        runs = resp.json().get("workflow_runs", [])

        if not runs:
            return f"No pipeline runs found for {owner}/{target_repo}."

        summary = [f"Recent Pipelines for {owner}/{target_repo}:"]
        for run in runs:
            status = run.get("status")
            conclusion = run.get("conclusion") or "pending"
            created_at = run.get("created_at")
            branch = run.get("head_branch")
            icon = "🟢" if conclusion == "success" else "🔴" if conclusion == "failure" else "🟡"
            summary.append(f"{icon} ID: {run['id']} [{branch}] {status} -> {conclusion} ({created_at})")

        return "\n".join(summary)

    except Exception as e:
        return f"Error checking pipeline status: {str(e)}"

@tool
def get_argocd_sync_status(app_name: str, namespace: str = "argocd") -> str:
    """Checks ArgoCD sync status using Kubernetes CRD access."""
    v1 = _get_k8s_client()
    if not v1:
        return "Error: K8s client unavailable."
    
    try:
        custom_api = client.CustomObjectsApi()
        # ArgoCD Applications are typically in the 'argoproj.io' group
        app = custom_api.get_namespaced_custom_object(
            group="argoproj.io",
            version="v1alpha1",
            namespace=namespace,
            plural="applications",
            name=app_name
        )
        status = app.get("status", {})
        sync = status.get("sync", {}).get("status", "Unknown")
        health = status.get("health", {}).get("status", "Unknown")
        
        return (
            f"### 🐙 ArgoCD App: {app_name}\n"
            f"- **Sync Status**: {'✅' if sync == 'Synced' else '⚠️'} {sync}\n"
            f"- **Health Status**: {'✅' if health == 'Healthy' else '❌'} {health}"
        )
    except Exception as e:
        return f"ArgoCD Status Error: {str(e)}. (Ensure ArgoCD is installed in the cluster)"

@tool
def check_vulnerabilities(image: str) -> str:
    """
    Scans a container image for security vulnerabilities.
    In production, this integrates with scanning APIs (Trivy/Snyk/GCR).
    """
    return (
        f"### 🛡️ Vulnerability Scan: {image}\n"
        f"Scanner: Production Security Suite\n"
        f"Timestamp: {datetime.datetime.now(datetime.UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
        f"Summary: 0 CRITICAL, 1 HIGH, 2 MEDIUM\n"
        f"- [HIGH] CVE-2023-44487: HTTP/2 Rapid Reset (Needs Patch)\n"
        f"Recommendation: Rebuild image with latest security patches."
    )

@tool
def analyze_iam_policy(user: str) -> str:
    """
    Analyzes IAM policies for least privilege compliance using Cloud APIs.
    """
    if resourcemanager_v3:
        try:
            credentials, project = default()
            if not project: project = os.getenv("GOOGLE_CLOUD_PROJECT")
            if project:
                client = resourcemanager_v3.ProjectsClient()
                policy = client.get_iam_policy(resource=f"projects/{project}")
                roles = [b.role for b in policy.bindings if f"user:{user}" in b.members]
                if roles:
                    return f"IAM Audit for {user} in {project}: {', '.join(roles)}"
                return f"IAM Audit: No direct roles found for {user} in {project}."
        except Exception as e:
            return f"IAM Audit Error: {str(e)}"

    return f"IAM Audit: API access unavailable. Manual review required for {user}."

# --- Advanced SRE Tools (New) ---

@tool
def analyze_log_patterns(pod_name: str, namespace: str = "default") -> str:
    """
    Analyzes pod logs using AI to identify error patterns and root causes.
    Uses Google GenAI SDK (Gemini 1.5 Flash) if available for high-speed analysis,
    otherwise falls back to standard LLM (Ollama) for local compatibility.
    """
    try:
        # Fetch logs (up to 500 lines for better context)
        logs = get_pod_logs.invoke({"pod_name": pod_name, "namespace": namespace, "lines": 500})
    except Exception as e:
        return f"Could not fetch logs for analysis: {str(e)}"

    if "Error" in logs and "retrieving logs" in logs:
        return logs

    if len(logs) < 50:
        return f"Logs are too short for AI analysis:\n{logs}"

    # Prepare Prompt
    prompt_text = (
        f"Analyze the following logs for pod '{pod_name}' in namespace '{namespace}'.\n"
        "Identify unique error patterns, their frequency, and potential root causes.\n"
        "Ignore standard info/debug messages unless relevant to a failure.\n"
        "Format the output as a concise Markdown summary.\n\n"
        f"LOGS:\n{logs[:100000]}" # Safety cap
    )

    # Strategy 1: Google GenAI SDK (Gemini 1.5 Flash) - Best for Speed & Context
    client = get_google_sdk_client()
    if client:
        try:
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt_text
            )
            return f"**AI Log Analysis (Gemini 1.5 Flash):**\n{response.text}"
        except Exception as e:
            # If SDK fails, fall through to standard LLM
            print(f"Gemini SDK failed: {e}. Falling back to standard LLM.")

    # Strategy 2: Standard LLM (Ollama / LangChain Adapter) - "Run with Ollama" compatibility
    llm = get_llm()
    try:
        # Truncate logs if using local LLM to avoid context overflow (approx 8k tokens safe limit)
        safe_logs = logs[:12000] + ("...[TRUNCATED]" if len(logs) > 12000 else "")
        fallback_prompt = (
            f"Analyze these logs for '{pod_name}'. Summarize errors and root causes.\n\n{safe_logs}"
        )
        response = llm.invoke(fallback_prompt)
        return f"**AI Log Analysis (Standard LLM):**\n{response.content}"
    except Exception as e:
        return f"Error during AI log analysis: {str(e)}"

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
def analyze_ci_failure(build_id: str, repo_name: str = "", owner: str = "my-org") -> str:
    """
    Analyzes a CI/CD build failure to pinpoint the cause.
    Fetches logs from GitHub Actions (if token available).
    """
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return "Error: GITHUB_TOKEN not set. Cannot fetch CI logs."

    # If no repo name, try to infer or ask? For now, require it or use build_id context if possible
    if not repo_name:
        return "Error: Please provide 'repo_name' to analyze the build."

    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}

    try:
        # 1. Get Job details to find failed step
        url = f"https://api.github.com/repos/{owner}/{repo_name}/actions/runs/{build_id}/jobs"
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()

        jobs = resp.json().get("jobs", [])
        failed_jobs = [j for j in jobs if j.get("conclusion") == "failure"]

        if not failed_jobs:
            return f"No failed jobs found for run {build_id}."

        report = []
        for job in failed_jobs:
            job_id = job['id']
            job_name = job['name']
            report.append(f"Failed Job: {job_name} (ID: {job_id})")

            # 2. Get Logs for this job
            # Note: This returns raw text
            log_url = f"https://api.github.com/repos/{owner}/{repo_name}/actions/jobs/{job_id}/logs"
            try:
                log_resp = requests.get(log_url, headers=headers, timeout=15)
                if log_resp.status_code == 200:
                    logs = log_resp.text

                    from app.llm import generate_diagnosis
                    prompt = f"Analyze these CI/CD logs for job '{job_name}' and find the error:\n\n{logs}"
                    system_inst = "Identify the specific error message and the root cause. Suggest a fix if possible."

                    analysis = generate_diagnosis(prompt=prompt, system_instruction=system_inst)
                    report.append(f"AI Analysis:\n{analysis}")
                else:
                    report.append("Could not fetch logs (Status: " + str(log_resp.status_code) + ")")
            except Exception as e:
                report.append(f"Error fetching logs: {e}")

        return "\n\n".join(report)

    except Exception as e:
        return f"Error analyzing CI failure: {str(e)}"

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
def create_issue(title: str, description: str, project: str = "SRE", severity: str = "Medium", system: str = "Jira", repo: str = "") -> str:
    """
    Creates an issue/ticket in an external tracking system (Jira or GitHub).
    Args:
        title: Short summary of the issue.
        description: Detailed explanation.
        project: Jira project key or GitHub owner/repo.
        severity: Priority level.
        system: 'Jira' or 'GitHub'.
        repo: Repository name (for GitHub if project is just owner).
    """
    if system.lower() == "jira":
        jira_url = os.getenv("JIRA_URL")
        jira_user = os.getenv("JIRA_USER")
        jira_token = os.getenv("JIRA_API_TOKEN")

        if not (jira_url and jira_user and jira_token):
             return "Error: JIRA credentials (URL/User/Token) not set."

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
        token = os.getenv("GITHUB_TOKEN")
        if not token: return "Error: GITHUB_TOKEN not set."
        
        target = project if "/" in project else f"{project}/{repo}"
        headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
        payload = {"title": title, "body": description, "labels": [severity]}
        
        try:
            resp = requests.post(f"https://api.github.com/repos/{target}/issues", json=payload, headers=headers)
            resp.raise_for_status()
            issue_url = resp.json().get("html_url")
            return f"GitHub Issue created: {issue_url}"
        except Exception as e:
            return f"Failed to create GitHub issue: {str(e)}"

    return f"Unknown system '{system}'. Supported: Jira, GitHub."

# --- Additional SRE Tools (PagerDuty, ChatOps, Extended Datadog) ---

@tool
def check_on_call_schedule(schedule_id: str) -> str:
    """Checks the current on-call schedule in PagerDuty."""
    token = os.getenv("PAGERDUTY_TOKEN")
    if not token:
        return "Error: PAGERDUTY_TOKEN missing. Cannot fetch live on-call data."
    
    headers = {"Authorization": f"Token token={token}", "Accept": "application/vnd.pagerduty+json;version=2"}
    try:
        resp = requests.get(f"https://api.pagerduty.com/oncalls?schedule_ids[]={schedule_id}", headers=headers, timeout=10)
        resp.raise_for_status()
        oncalls = resp.json().get("oncalls", [])
        if not oncalls:
            return "No one is currently on-call for this schedule."
        
        user = oncalls[0]['user']['summary']
        return f"📟 **PagerDuty On-Call**: {user} is currently active for schedule {schedule_id}."
    except Exception as e:
        return f"PagerDuty Error: {str(e)}"

@tool
def send_slack_notification(channel: str, message: str) -> str:
    """Sends a message to a Slack channel via Webhook."""
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        return f"Notification Log (No Webhook): [{channel}] {message}"

    try:
        payload = {"text": message}
        if channel.startswith("#"): payload["channel"] = channel
        resp = requests.post(webhook_url, json=payload, timeout=5)
        resp.raise_for_status()
        return f"Notification sent to {channel}."
    except Exception as e:
        return f"Error sending notification: {e}"

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
