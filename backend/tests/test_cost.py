import pytest
from unittest.mock import patch
from app.tools.cost import estimate_gcp_cost
import os

def test_estimate_gcp_cost_success(monkeypatch):
    """
    Test successful execution of estimate_gcp_cost, mocking GCP resource list and LLM output.
    """
    # Force use of mocks to make it predictable
    monkeypatch.setenv("USE_REAL_TOOLS", "false")

    with patch("app.tools.mocks.list_compute_instances._run", return_value="Instance: vm-1, Type: e2-medium"), \
         patch("app.tools.mocks.get_gcp_sql_instances._run", return_value="Instance: sql-1, Type: db-f1-micro"), \
         patch("app.tools.cost.get_google_sdk_client") as mock_sdk, \
         patch("app.tools.cost.get_llm") as mock_llm:

        # Ensure it falls back to standard LLM for testing
        mock_sdk.return_value = None

        class MockLLMResponse:
            content = "- **Compute Engine**: $25.00\n- **Cloud SQL**: $10.00\n- **Total Estimated Monthly Cost**: $35.00"

        mock_llm.return_value.invoke.return_value = MockLLMResponse()

        result = estimate_gcp_cost.invoke({})

        assert "Total Estimated Monthly Cost" in result
        assert "$35.00" in result

def test_estimate_gcp_cost_gemini():
    """
    Test successful execution with Gemini SDK.
    """
    os.environ["USE_REAL_TOOLS"] = "false"

    with patch("app.tools.mocks.list_compute_instances._run", return_value="vm"), \
         patch("app.tools.mocks.get_gcp_sql_instances._run", return_value="sql"), \
         patch("app.tools.cost.get_google_sdk_client") as mock_sdk:

        class MockGeminiResponse:
            text = "Gemini Cost Estimate: $100.00"

        mock_sdk.return_value.models.generate_content.return_value = MockGeminiResponse()

        result = estimate_gcp_cost.invoke({})

        assert "Gemini Cost Estimate: $100.00" in result

def test_estimate_gcp_cost_resource_error():
    """
    Test when underlying resource gathering fails, but LLM still generates an estimate
    (or states it can't).
    """
    os.environ["USE_REAL_TOOLS"] = "false"

    with patch("app.tools.mocks.list_compute_instances._run", side_effect=Exception("API Error")), \
         patch("app.tools.mocks.get_gcp_sql_instances._run", side_effect=Exception("API Error")), \
         patch("app.tools.cost.get_google_sdk_client") as mock_sdk, \
         patch("app.tools.cost.get_llm") as mock_llm:

        mock_sdk.return_value = None

        class MockLLMResponse:
            content = "Could not estimate due to missing resource data."

        mock_llm.return_value.invoke.return_value = MockLLMResponse()

        result = estimate_gcp_cost.invoke({})

        assert "Could not estimate" in result
