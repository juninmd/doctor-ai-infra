import pytest
from unittest.mock import MagicMock, patch
from app.tools.reasoning import generate_hypothesis

@patch("app.tools.reasoning.get_google_sdk_client")
@patch("app.tools.reasoning.get_llm")
def test_generate_hypothesis_gemini(mock_get_llm, mock_get_client):
    # Setup Gemini Mock
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = MagicMock()
    mock_response.text = '[{"hypothesis": "Network Issue", "validation_step": "Check connectivity", "probability": "High"}]'
    mock_client.models.generate_content.return_value = mock_response

    # Invoke
    result = generate_hypothesis.invoke({"context": "System is slow"})

    # Verify
    assert "Network Issue" in result
    mock_client.models.generate_content.assert_called_once()
    mock_get_llm.assert_not_called()

@patch("app.tools.reasoning.get_google_sdk_client")
@patch("app.tools.reasoning.get_llm")
def test_generate_hypothesis_fallback(mock_get_llm, mock_get_client):
    # Setup Fallback (Client returns None)
    mock_get_client.return_value = None

    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.content = '[{"hypothesis": "CPU Spike", "validation_step": "Check top", "probability": "Medium"}]'
    mock_llm.invoke.return_value = mock_response
    mock_get_llm.return_value = mock_llm

    # Invoke
    result = generate_hypothesis.invoke({"context": "System is slow"})

    # Verify
    assert "CPU Spike" in result
    mock_llm.invoke.assert_called_once()
