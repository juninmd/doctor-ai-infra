import pytest
import os
import base64
from unittest.mock import patch
from app.tools.code import read_repo_file
from app.tools.real import list_recent_commits, create_issue

@patch.dict(os.environ, {"GITHUB_TOKEN": "fake_token"}, clear=True)
@patch('app.tools.real.requests.get')
def test_list_recent_commits_success(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = [{
        "sha": "1234567890",
        "commit": {
            "message": "Fix bug",
            "author": {"name": "Jules", "date": "2026-04-22T00:00:00Z"}
        }
    }]

    result = list_recent_commits.invoke({"owner": "my-org", "repo": "test"})
    assert "Fix bug" in result
    assert "1234567" in result

@patch.dict(os.environ, {"GITHUB_TOKEN": "fake_token"}, clear=True)
@patch('app.tools.code.requests.get')
def test_read_repo_file_success(mock_get):
    mock_get.return_value.status_code = 200
    encoded_content = base64.b64encode(b"Hello World").decode("utf-8")
    mock_get.return_value.json.return_value = {"content": encoded_content}

    result = read_repo_file.invoke({"repo": "my-org/test", "file_path": "README.md"})
    assert "Hello World" in result

@patch.dict(os.environ, {"JIRA_URL": "http://jira", "JIRA_USER": "user", "JIRA_API_TOKEN": "token"}, clear=True)
@patch('app.tools.real.requests.post')
def test_create_issue_success(mock_post):
    mock_post.return_value.status_code = 201
    mock_post.return_value.json.return_value = {"key": "SRE-123"}

    result = create_issue.invoke({
        "title": "System Down",
        "description": "500 errors",
        "project": "SRE",
        "severity": "High",
        "system": "Jira"
    })
    assert "SRE-123" in result
