import pytest
from unittest.mock import MagicMock, patch
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db import Base

# Ensure backend is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def db_session():
    """
    Creates a fresh in-memory database for each test and patches SessionLocal.
    """
    # Create engine and tables
    # Use StaticPool to ensure the same in-memory connection is shared
    # across multiple session creations within the test.
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)

    # Create a session factory bound to this engine
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create a session for the test itself (if needed)
    session = TestingSessionLocal()

    # Patch app.db.SessionLocal to use our testing factory
    # This ensures that when tools call SessionLocal(), they get a session connected to our test DB
    with patch("app.db.SessionLocal", side_effect=TestingSessionLocal):
        # We also need to patch it in specific tools if they imported it directly
        # But since we can't easily patch all, we rely on them importing from app.db
        # or we patch specifically in the test file if needed.
        # For incident tools, we know they use app.db.SessionLocal (or from app.db import SessionLocal)
        # If they use 'from app.db import SessionLocal', patching 'app.db.SessionLocal' might not work
        # if the module is already imported.
        # So we patch the reference in app.tools.incident as well.
        # And app.rag used by initialize_rag
        p1 = patch("app.tools.incident.SessionLocal", side_effect=TestingSessionLocal)
        p2 = patch("app.rag.SessionLocal", side_effect=TestingSessionLocal)
        p3 = patch("app.tools.runbooks.SessionLocal", side_effect=TestingSessionLocal) # Just in case

        with p1, p2, p3:
            yield session

    # Cleanup
    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def mock_rag_engine():
    """Mocks the RAG engine to avoid vector store calls."""
    mock_rag = MagicMock()
    mock_rag.search.return_value = []
    mock_rag.count.return_value = 0

    # Patch global instance in app.rag
    p1 = patch("app.rag.rag_engine", mock_rag)
    # Patch reference in incident tool
    p2 = patch("app.tools.incident.rag_engine", mock_rag)

    with p1, p2:
        yield mock_rag

@pytest.fixture
def mock_llm():
    """Mocks the LLM to return predictable text."""
    mock_chat = MagicMock()
    # Default response
    mock_chat.invoke.return_value = MagicMock(content="Mocked LLM Response")

    # Patch get_llm to return our mock
    with patch("app.llm.get_llm", return_value=mock_chat) as mock_get_llm:
        with patch("app.tools.incident.get_llm", return_value=mock_chat):
             yield mock_chat

@pytest.fixture
def mock_google_sdk():
    """Mocks the Google GenAI SDK."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Mocked Gemini Response"
    mock_client.models.generate_content.return_value = mock_response

    with patch("app.llm.get_google_sdk_client", return_value=mock_client) as mock_get_sdk:
        with patch("app.tools.incident.get_google_sdk_client", return_value=mock_client):
            yield mock_client
