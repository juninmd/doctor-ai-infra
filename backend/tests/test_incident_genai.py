import pytest
from unittest.mock import patch, MagicMock
from app.tools.incident import generate_postmortem
from app.db import SessionLocal, Incident, PostMortem

@pytest.fixture
def mock_db_session():
    with patch("app.tools.incident.SessionLocal") as mock_session:
        session = MagicMock()
        mock_session.return_value = session
        yield session

@pytest.fixture
def mock_google_client():
    with patch("app.tools.incident.get_google_sdk_client") as mock_client:
        yield mock_client

@pytest.fixture
def mock_get_llm():
    with patch("app.tools.incident.get_llm") as mock_llm:
        yield mock_llm

def test_generate_postmortem_gemini_sdk(mock_db_session, mock_google_client):
    """Test that Google SDK is used when available."""
    # Setup Incident
    incident_id = "inc-123"
    mock_incident = Incident(id=incident_id, title="Test Incident", severity="SEV-1", description="Test", status="RESOLVED")
    # Mock DB query
    mock_db_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [] # No events
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_incident

    # Mock SDK Client
    client_instance = MagicMock()
    mock_google_client.return_value = client_instance
    client_instance.models.generate_content.return_value.text = "SDK Generated Report"

    # Execute
    result = generate_postmortem.invoke({"incident_id": incident_id})

    # Verify
    assert "Post-Mortem generated" in result
    assert "SDK Generated Report" in result
    client_instance.models.generate_content.assert_called_once()

    # Verify DB save
    args, _ = mock_db_session.add.call_args
    saved_obj = args[0]
    assert isinstance(saved_obj, PostMortem)
    assert saved_obj.content == "SDK Generated Report"

def test_generate_postmortem_fallback_llm(mock_db_session, mock_google_client, mock_get_llm):
    """Test fallback to standard LLM when SDK is missing."""
    # Setup Incident
    incident_id = "inc-456"
    mock_incident = Incident(id=incident_id, title="Test Incident Fallback", severity="SEV-2", description="Test", status="RESOLVED")
    mock_db_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_incident

    # Mock SDK Client returning None
    mock_google_client.return_value = None

    # Mock LLM and Chain
    mock_llm_instance = MagicMock()
    mock_get_llm.return_value = mock_llm_instance

    # Mocking the chain execution is tricky because of the pipe operator.
    # We will assume the code reaches `res = chain.invoke(...)`.
    # If `prompt | llm` returns a mock, then calling invoke on it should work.
    # To ensure `prompt | llm` returns a mock that we control, we might need to mock ChatPromptTemplate too.

    with patch("app.tools.incident.ChatPromptTemplate") as MockPrompt:
        # prompt | llm -> chain
        mock_prompt_instance = MockPrompt.from_messages.return_value
        mock_chain = MagicMock()
        mock_prompt_instance.__or__.return_value = mock_chain

        mock_chain.invoke.return_value.content = "Fallback LLM Report"

        # Execute
        result = generate_postmortem.invoke({"incident_id": incident_id})

        # Verify
        assert "Post-Mortem generated" in result
        assert "Fallback LLM Report" in result
        mock_chain.invoke.assert_called_once()
