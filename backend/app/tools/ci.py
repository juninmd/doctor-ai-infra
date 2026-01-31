from langchain_core.tools import tool
import os
import requests
from typing import Optional

def _get_github_headers():
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return None
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

@tool
def check_github_repos(org: str = "my-org") -> str:
    """
    Checks the status of GitHub repositories and returns a list of recent repos.
    If GITHUB_TOKEN is set, it queries the GitHub API.
    """
    headers = _get_github_headers()
    if not headers:
        return f"Simulated: Repositories in {org}: 'backend-service', 'frontend-app', 'infra-config' (Set GITHUB_TOKEN for real data)"

    try:
        url = f"https://api.github.com/orgs/{org}/repos?sort=updated&per_page=5"
        # If org is a user, the url is /users/{username}/repos
        # Let's try org first, then user if 404?
        # For simplicity, we assume org or user provided correctly, but usually /users/:username/repos is safer for personal

        resp = requests.get(url, headers=headers, timeout=10)

        if resp.status_code == 404:
             # Try as user
             url = f"https://api.github.com/users/{org}/repos?sort=updated&per_page=5"
             resp = requests.get(url, headers=headers, timeout=10)

        if resp.status_code == 200:
            repos = resp.json()
            if not repos:
                return f"No repositories found for {org}."

            repo_list = []
            for r in repos:
                name = r.get('name')
                desc = r.get('description') or "No description"
                url = r.get('html_url')
                repo_list.append(f"- {name}: {desc} ({url})")
            return f"Recent Repositories in {org}:\n" + "\n".join(repo_list)

        return f"GitHub API Error: {resp.status_code} - {resp.text}"
    except Exception as e:
        return f"Error connecting to GitHub: {str(e)}"

@tool
def get_pr_status(repo: str, pr_id: int) -> str:
    """
    Checks the status of a specific Pull Request.
    Args:
        repo: Repository name (e.g., 'owner/repo').
        pr_id: Pull Request number.
    """
    headers = _get_github_headers()
    if not headers:
        return f"Simulated: PR #{pr_id} in {repo} is OPEN. (Set GITHUB_TOKEN for real data)"

    try:
        if "/" not in repo:
            return "Error: Repo must be in format 'owner/repo'."

        url = f"https://api.github.com/repos/{repo}/pulls/{pr_id}"
        resp = requests.get(url, headers=headers, timeout=10)

        if resp.status_code == 200:
            pr = resp.json()
            title = pr.get('title')
            state = pr.get('state')
            merged = pr.get('merged')
            user = pr.get('user', {}).get('login')

            status = state.upper()
            if merged:
                status = "MERGED"

            return f"PR #{pr_id} '{title}' is {status}. Author: {user}."
        elif resp.status_code == 404:
            return f"PR #{pr_id} not found in {repo}."

        return f"GitHub API Error: {resp.status_code} - {resp.text}"
    except Exception as e:
        return f"Error checking PR: {str(e)}"

@tool
def check_pipeline_status(repo: str) -> str:
    """
    Checks the status of recent CI/CD pipeline runs (GitHub Actions).
    Args:
        repo: Repository name (e.g., 'owner/repo').
    """
    headers = _get_github_headers()
    if not headers:
        return f"Simulated: Pipeline for {repo} - Last run: FAILED (Main Branch). (Set GITHUB_TOKEN for real data)"

    try:
        if "/" not in repo:
            return "Error: Repo must be in format 'owner/repo'."

        url = f"https://api.github.com/repos/{repo}/actions/runs?per_page=3"
        resp = requests.get(url, headers=headers, timeout=10)

        if resp.status_code == 200:
            runs = resp.json().get("workflow_runs", [])
            if not runs:
                return f"No workflow runs found for {repo}."

            results = []
            for run in runs:
                name = run.get('name')
                status = run.get('status') # queued, in_progress, completed
                conclusion = run.get('conclusion') # success, failure, etc.
                branch = run.get('head_branch')
                run_id = run.get('id')

                results.append(f"- ID {run_id}: {name} ({branch}) -> {status.upper()} ({conclusion or 'Pending'})")

            return f"Recent Pipeline Runs for {repo}:\n" + "\n".join(results)

        return f"GitHub API Error: {resp.status_code} - {resp.text}"
    except Exception as e:
        return f"Error checking pipeline: {str(e)}"

@tool
def analyze_ci_failure(build_id: str, repo: str) -> str:
    """
    Analyzes a specific CI build failure to pinpoint the cause.
    Args:
        build_id: The ID of the workflow run.
        repo: Repository name (e.g., 'owner/repo').
    """
    headers = _get_github_headers()
    if not headers:
        return f"Simulated: Analysis for Build {build_id} in {repo}: Failed at 'Unit Tests' step. Logs indicate 'AssertionError'. (Set GITHUB_TOKEN for real data)"

    try:
        # Get jobs for the run
        url = f"https://api.github.com/repos/{repo}/actions/runs/{build_id}/jobs"
        resp = requests.get(url, headers=headers, timeout=10)

        if resp.status_code == 200:
            jobs = resp.json().get("jobs", [])
            failed_jobs = [j for j in jobs if j.get("conclusion") == "failure"]

            if not failed_jobs:
                return f"Build {build_id} has no failed jobs reported."

            report = [f"Analysis for Build {build_id}:"]
            for job in failed_jobs:
                job_name = job.get("name")
                steps = job.get("steps", [])
                failed_steps = [s for s in steps if s.get("conclusion") == "failure"]

                report.append(f"Job '{job_name}' FAILED.")
                for step in failed_steps:
                    step_name = step.get("name")
                    # We can't easily get full logs via this endpoint, but we can point to it
                    report.append(f"  - Step '{step_name}' failed.")

            return "\n".join(report)

        return f"GitHub API Error: {resp.status_code} - {resp.text}"
    except Exception as e:
        return f"Error analyzing CI failure: {str(e)}"

@tool
def list_recent_builds(repo: str, limit: int = 5) -> str:
    """
    Lists recent workflow runs for a repository.
    Args:
        repo: Repository name (e.g., 'owner/repo').
        limit: Number of builds to list.
    """
    headers = _get_github_headers()
    if not headers:
        return f"Simulated: Recent builds for {repo}: [101] Success, [102] Failed. (Set GITHUB_TOKEN for real data)"

    try:
        if "/" not in repo:
             return "Error: Repo must be in format 'owner/repo'."

        url = f"https://api.github.com/repos/{repo}/actions/runs?per_page={limit}"
        resp = requests.get(url, headers=headers, timeout=10)

        if resp.status_code == 200:
             runs = resp.json().get("workflow_runs", [])
             summary = []
             for run in runs:
                 summary.append(f"Build {run.get('id')} ({run.get('head_branch')}): {run.get('conclusion') or run.get('status')}")
             return "\n".join(summary)
        return f"Error fetching builds: {resp.status_code}"
    except Exception as e:
        return f"Exception: {str(e)}"
