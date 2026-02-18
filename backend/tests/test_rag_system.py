import pytest
from unittest.mock import MagicMock, patch
import app.rag  # Import the module directly
from app.rag import initialize_rag
from app.db import Service, Runbook, Incident
import os

def test_rag_initialization(db_session, mock_rag_engine):
    # Setup data in the in-memory DB
    s1 = Service(name="service-a", description="A great service", owner="Team A", tier="1")
    r1 = Runbook(name="restart-db", description="How to restart DB", implementation_key="restart_db_func")
    db_session.add(s1)
    db_session.add(r1)
    db_session.commit()

    # Verify data is in DB
    assert db_session.query(Service).filter(Service.name == "service-a").count() == 1
    assert db_session.query(Runbook).filter(Runbook.name == "restart-db").count() == 1

    # Create a mock for SessionLocal that returns our fixture session
    mock_session_factory = MagicMock(return_value=db_session)

    # Patch the rag_engine AND SessionLocal on the imported module object directly
    # This ensures we use the test DB and test Mock RAG, regardless of import aliasing
    with patch.object(app.rag, "rag_engine", mock_rag_engine), \
         patch.object(app.rag, "SessionLocal", mock_session_factory), \
         patch.dict("os.environ", {"FORCE_RAG_INDEX": "true"}):

            # Verify patch is active
            assert app.rag.rag_engine is mock_rag_engine
            # assert app.rag.SessionLocal() is db_session # Can't call twice if session closes?
            # db_session fixture yields a session.

            # Run init
            initialize_rag()

    # Verify add_documents was called on the mock engine
    assert mock_rag_engine.add_documents.called

    # Inspect the documents passed to add_documents
    # call_args[0] is positional args, [0] is the first arg (list of docs)
    docs = mock_rag_engine.add_documents.call_args[0][0]

    # Check we have at least service and runbook documents
    service_docs = [d for d in docs if d.metadata.get('type') == 'service']
    runbook_docs = [d for d in docs if d.metadata.get('type') == 'runbook']

    # Robust check: Ensure our test data is present
    service_names = [d.metadata['name'] for d in service_docs]
    runbook_names = [d.metadata['name'] for d in runbook_docs]

    assert "service-a" in service_names
    assert "restart-db" in runbook_names

    # Also verify we are NOT seeing the polluted data (optional, but good for sanity)
    assert "auth-service" not in service_names

def test_rag_search_via_mock(mock_rag_engine):
    # Test that we can use the mock interface
    mock_rag_engine.search.return_value = ["Doc 1", "Doc 2"]

    # In a real scenario, this would be called by a tool.
    # We verify the mock is set up correctly.
    results = mock_rag_engine.search("query")
    assert results == ["Doc 1", "Doc 2"]
