import pytest
from unittest.mock import patch, MagicMock
from app.tools.knowledge import add_knowledge_base_item

def test_add_knowledge_base_item():
    with patch("app.tools.knowledge.rag_engine") as mock_rag:
        # Mock successful addition
        result = add_knowledge_base_item.invoke({"content": "This is a test note", "category": "test_cat"})

        # Verify rag_engine.add_documents was called
        assert mock_rag.add_documents.called
        docs = mock_rag.add_documents.call_args[0][0]
        assert len(docs) == 1
        assert docs[0].page_content == "This is a test note"
        assert docs[0].metadata["type"] == "test_cat"

        assert "Successfully added item" in result

def test_add_knowledge_base_item_error():
    with patch("app.tools.knowledge.rag_engine") as mock_rag:
        mock_rag.add_documents.side_effect = Exception("RAG error")
        result = add_knowledge_base_item.invoke({"content": "Fail me"})
        assert "Error adding to Knowledge Base: RAG error" in result
