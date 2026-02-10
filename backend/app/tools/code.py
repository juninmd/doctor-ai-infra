from langchain_core.tools import tool
import requests
import base64
import os
from app.llm import get_google_sdk_client, get_llm

def _fetch_file_content(repo: str, file_path: str) -> str:
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return "Error: GITHUB_TOKEN not set."

    headers = {"Authorization": f"token {token}"}
    try:
        url = f"https://api.github.com/repos/{repo}/contents/{file_path}"
        resp = requests.get(url, headers=headers, timeout=10)

        if resp.status_code == 404:
            return f"File '{file_path}' not found in '{repo}'."

        resp.raise_for_status()
        data = resp.json()

        if "content" not in data:
            return f"Error: No content found (is it a directory?)"

        content = base64.b64decode(data["content"]).decode("utf-8")
        return content
    except Exception as e:
        return f"Error reading file: {str(e)}"

@tool
def read_repo_file(repo: str, file_path: str) -> str:
    """
    Reads the content of a file from a GitHub repository.
    Args:
        repo: The GitHub repository (e.g., "owner/repo").
        file_path: The path to the file within the repository.
    """
    return _fetch_file_content(repo, file_path)

@tool
def list_repo_files(repo: str, path: str = "") -> str:
    """
    Lists files in a GitHub repository directory.
    Args:
        repo: The GitHub repository (e.g., "owner/repo").
        path: The directory path to list (default root).
    """
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return "Error: GITHUB_TOKEN not set."

    headers = {"Authorization": f"token {token}"}
    try:
        url = f"https://api.github.com/repos/{repo}/contents/{path}"
        resp = requests.get(url, headers=headers, timeout=10)

        if resp.status_code == 404:
            return f"Path '{path}' not found in '{repo}'."

        resp.raise_for_status()
        items = resp.json()

        if isinstance(items, dict): # Single file
            return f"Item is a file: {items['name']}"

        file_list = []
        for item in items:
            type_icon = "📁" if item["type"] == "dir" else "📄"
            file_list.append(f"{type_icon} {item['name']}")

        return "\n".join(file_list)
    except Exception as e:
        return f"Error listing files: {str(e)}"

@tool
def generate_code_fix(repo: str, file_path: str, issue_description: str) -> str:
    """
    Generates a code fix for a specific file in a GitHub repository using AI.
    Fetches the file content, analyzes the issue, and returns the full fixed file content.

    Args:
        repo: The GitHub repository (e.g., "owner/repo").
        file_path: The path to the file within the repository.
        issue_description: A description of the bug or issue to fix.
    """
    content = _fetch_file_content(repo, file_path)
    if content.startswith("Error"):
        return content

    # Generate Fix using AI
    prompt = (
        f"You are an expert Software Engineer (Bits AI SRE).\n"
        f"I have a file `{file_path}` in repo `{repo}` that has an issue.\n\n"
        f"ISSUE DESCRIPTION:\n{issue_description}\n\n"
        f"FILE CONTENT:\n```\n{content}\n```\n\n"
        "Please provide the FIXED version of the file.\n"
        "Output ONLY the code, no markdown fencing or explanations, just the raw code ready to be saved."
    )

    # Strategy 1: Google GenAI SDK (Best 2026 Implementation)
    client = get_google_sdk_client()
    if client:
        try:
            # Use `models.generate_content` as per v1.0 SDK
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt,
                config={
                    "temperature": 0.2, # Lower temperature for code precision
                }
            )
            return response.text.strip().replace("```python", "").replace("```", "")
        except Exception as e:
            print(f"Gemini SDK failed: {e}. Falling back to standard LLM.")

    # Strategy 2: Standard LLM Fallback (Ollama compatibility)
    try:
        llm = get_llm()
        # Truncate content if necessary for local models
        if len(prompt) > 12000:
            prompt = prompt[:12000] + "\n...[TRUNCATED]"

        response = llm.invoke(prompt)
        return response.content.strip().replace("```python", "").replace("```", "")
    except Exception as e:
        return f"Error generating fix: {str(e)}"

@tool
def create_github_pr(repo: str, file_path: str, new_content: str, title: str, body: str, branch_name: str) -> str:
    """
    Creates a Pull Request on GitHub with the specified file changes.

    Args:
        repo: The GitHub repository (e.g., "owner/repo").
        file_path: The path of the file to update.
        new_content: The new content of the file.
        title: Title of the Pull Request.
        body: Description of the Pull Request.
        branch_name: The name of the new branch to create (e.g., "fix/issue-123").
    """
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return "Error: GITHUB_TOKEN not set."

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    try:
        # 1. Get default branch (usually main or master)
        resp = requests.get(f"https://api.github.com/repos/{repo}", headers=headers)
        resp.raise_for_status()
        default_branch = resp.json().get("default_branch", "main")

        # 2. Get SHA of the default branch
        resp = requests.get(f"https://api.github.com/repos/{repo}/git/ref/heads/{default_branch}", headers=headers)
        resp.raise_for_status()
        base_sha = resp.json()["object"]["sha"]

        # 3. Create new branch
        # Check if branch exists first
        branch_check = requests.get(f"https://api.github.com/repos/{repo}/git/ref/heads/{branch_name}", headers=headers)
        if branch_check.status_code == 404:
            resp = requests.post(
                f"https://api.github.com/repos/{repo}/git/refs",
                headers=headers,
                json={"ref": f"refs/heads/{branch_name}", "sha": base_sha}
            )
            if resp.status_code != 201:
                 return f"Error creating branch '{branch_name}': {resp.text}"
        else:
            # Branch exists, maybe update it? Or fail?
            # Ideally we'd use it.
            pass

        # 4. Get file SHA (needed for update)
        # MUST fetch from the target branch to avoid 409 Conflict if file exists/changed there
        resp = requests.get(f"https://api.github.com/repos/{repo}/contents/{file_path}?ref={branch_name}", headers=headers)
        file_sha = None
        if resp.status_code == 200:
            file_sha = resp.json().get("sha")

        # 5. Update File
        # Content must be base64 encoded
        encoded_content = base64.b64encode(new_content.encode("utf-8")).decode("utf-8")
        payload = {
            "message": f"fix: update {file_path}",
            "content": encoded_content,
            "branch": branch_name
        }
        if file_sha:
            payload["sha"] = file_sha

        resp = requests.put(
            f"https://api.github.com/repos/{repo}/contents/{file_path}",
            headers=headers,
            json=payload
        )
        resp.raise_for_status()

        # 6. Create Pull Request
        pr_payload = {
            "title": title,
            "body": body,
            "head": branch_name,
            "base": default_branch
        }
        resp = requests.post(
            f"https://api.github.com/repos/{repo}/pulls",
            headers=headers,
            json=pr_payload
        )
        if resp.status_code == 422:
            # Likely exists, try to return existing
            return "Error: Pull Request already exists or no changes."

        resp.raise_for_status()

        pr_url = resp.json().get("html_url")
        return f"Success! Pull Request created: {pr_url}"

    except Exception as e:
        return f"Error creating Pull Request: {str(e)}"
