import os
from typing import List, Dict, Optional
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from app.db import SessionLocal, Incident
from app.tools.runbooks import RUNBOOKS, SERVICE_CATALOG

CHROMA_DB_DIR = "./chroma_db"

class RAGEngine:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        self.vector_store = Chroma(
            collection_name="sre_knowledge_base",
            embedding_function=self.embeddings,
            persist_directory=CHROMA_DB_DIR
        )

    def add_documents(self, documents: List[Document]):
        """Adds documents to the vector store."""
        if not documents:
            return
        self.vector_store.add_documents(documents)

    def search(self, query: str, k: int = 5) -> List[Document]:
        """Searches the vector store for relevant documents."""
        return self.vector_store.similarity_search(query, k=k)

    def reset(self):
        """Resets the vector store (clears all data)."""
        self.vector_store.delete_collection()
        self.vector_store = Chroma(
            collection_name="sre_knowledge_base",
            embedding_function=self.embeddings,
            persist_directory=CHROMA_DB_DIR
        )

rag_engine = RAGEngine()

def initialize_rag():
    """
    Initializes the RAG system by indexing Runbooks, Service Catalog, and Past Incidents.
    This function is designed to be idempotent-ish or run on startup.
    For this implementation, we reset and re-index to ensure freshness.
    """
    print("Initializing RAG Knowledge Base...")

    # Optional: Clear existing to avoid duplicates on restart
    # In production, you'd check for existence or use IDs.
    rag_engine.reset()

    docs = []

    # 1. Index Runbooks
    for name, desc in RUNBOOKS.items():
        doc = Document(
            page_content=f"Runbook: {name}\nDescription: {desc}",
            metadata={"type": "runbook", "name": name, "source": "automation_library"}
        )
        docs.append(doc)

    # 2. Index Service Catalog
    for name, details in SERVICE_CATALOG.items():
        content = (
            f"Service: {name}\n"
            f"Description: {details.get('description')}\n"
            f"Owner: {details.get('owner')}\n"
            f"Tier: {details.get('tier')}\n"
            f"Dependencies: {', '.join(details.get('dependencies', []))}"
        )
        doc = Document(
            page_content=content,
            metadata={"type": "service", "name": name, "source": "service_catalog"}
        )
        docs.append(doc)

    # 3. Index Past Incidents (from SQLite)
    db = SessionLocal()
    try:
        incidents = db.query(Incident).filter(Incident.status != 'OPEN').all()
        for inc in incidents:
            content = (
                f"Incident Title: {inc.title}\n"
                f"Severity: {inc.severity}\n"
                f"Status: {inc.status}\n"
                f"Description: {inc.description}\n"
                f"Updates: {inc.updates}"
            )
            doc = Document(
                page_content=content,
                metadata={"type": "incident", "id": inc.id, "source": "incident_db"}
            )
            docs.append(doc)
    except Exception as e:
        print(f"Error indexing incidents: {e}")
    finally:
        db.close()

    if docs:
        rag_engine.add_documents(docs)
        print(f"RAG Initialization Complete. Indexed {len(docs)} documents.")
    else:
        print("RAG Initialization: No documents to index.")
