import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Ensure backend in path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.tools.code import generate_code_fix, create_github_pr

class TestCodeTools(unittest.TestCase):

    @patch("app.tools.code.get_google_sdk_client")
    @patch("app.tools.code.requests")
    @patch("app.tools.code.os.getenv")
    def test_generate_code_fix_sdk(self, mock_getenv, mock_requests, mock_get_sdk):
        # Setup
        mock_getenv.return_value = "fake_token"

        # Mock file fetch
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"content": "cHJpbnQoImhlbGxvIikK"} # print("hello") in base64
        mock_requests.get.return_value = mock_resp

        # Mock SDK
        mock_client = MagicMock()
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "print('fixed')"
        mock_model.generate_content.return_value = mock_response
        mock_client.models = mock_model
        mock_get_sdk.return_value = mock_client

        # Execute
        result = generate_code_fix.invoke({
            "repo": "test/repo",
            "file_path": "main.py",
            "issue_description": "Fix typo"
        })

        # Assert
        self.assertEqual(result, "print('fixed')")
        mock_model.generate_content.assert_called_once()
        mock_requests.get.assert_called()

    @patch("app.tools.code.requests")
    @patch("app.tools.code.os.getenv")
    def test_create_github_pr(self, mock_getenv, mock_requests):
        mock_getenv.return_value = "fake_token"

        # Sequence of calls:
        # 1. GET repo (default branch)
        # 2. GET ref heads/main (sha)
        # 3. GET ref heads/branch (check exist - 404)
        # 4. POST git/refs (create branch)
        # 5. GET contents/file (file sha)
        # 6. PUT contents/file (update)
        # 7. POST pulls (create PR)

        # We need side_effect for requests to return different mocks

        resp_repo = MagicMock()
        resp_repo.json.return_value = {"default_branch": "main"}

        resp_sha = MagicMock()
        resp_sha.json.return_value = {"object": {"sha": "base_sha"}}

        resp_check_branch = MagicMock()
        resp_check_branch.status_code = 404 # Branch doesn't exist

        resp_create_branch = MagicMock()
        resp_create_branch.status_code = 201

        resp_file = MagicMock()
        resp_file.status_code = 200
        resp_file.json.return_value = {"sha": "file_sha"}

        resp_update = MagicMock()
        resp_update.raise_for_status.return_value = None

        resp_pr = MagicMock()
        resp_pr.raise_for_status.return_value = None
        resp_pr.json.return_value = {"html_url": "http://pr/1"}

        # Order of get calls: repo, ref/heads/main, ref/heads/newbranch, contents/file
        mock_requests.get.side_effect = [resp_repo, resp_sha, resp_check_branch, resp_file]

        # Order of post/put: post(ref), put(file), post(pr)
        # requests.post called twice (ref, pr), put called once

        # Setup post side effects based on URL or just order
        # It's harder to mock mixed verbs with side_effect list on module.requests unless we mock specific methods
        mock_requests.post.side_effect = [resp_create_branch, resp_pr]
        mock_requests.put.return_value = resp_update

        result = create_github_pr.invoke({
            "repo": "test/repo",
            "file_path": "main.py",
            "new_content": "print('fixed')",
            "title": "Fix",
            "body": "Fixed it",
            "branch_name": "fix/test"
        })

        self.assertIn("Success", result)
        self.assertIn("http://pr/1", result)

        # Verify calls
        mock_requests.post.assert_any_call(
            "https://api.github.com/repos/test/repo/git/refs",
            headers=unittest.mock.ANY,
            json={"ref": "refs/heads/fix/test", "sha": "base_sha"}
        )

if __name__ == "__main__":
    unittest.main()
