import pytest
from unittest.mock import MagicMock, patch
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
    assert db_session.query(Service).count() == 1
    assert db_session.query(Runbook).count() == 1

    # Mock rag_engine to be the mock object passed in (explicitly, to be safe)
    # We rely on conftest for SessionLocal, but we double check app.rag.rag_engine
    with patch("app.rag.rag_engine", mock_rag_engine), \
         patch.dict("os.environ", {"FORCE_RAG_INDEX": "true"}):
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

    assert len(service_docs) >= 1
    assert service_docs[0].metadata['name'] == "service-a"

    assert len(runbook_docs) >= 1
    assert runbook_docs[0].metadata['name'] == "restart-db"

def test_rag_search_via_mock(mock_rag_engine):
    # Test that we can use the mock interface
    mock_rag_engine.search.return_value = ["Doc 1", "Doc 2"]

    # In a real scenario, this would be called by a tool.
    # We verify the mock is set up correctly.
    results = mock_rag_engine.search("query")
    assert results == ["Doc 1", "Doc 2"]
