import sys
import os
import uuid

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

from app.rag import initialize_rag, rag_engine
from app.db import SessionLocal, Incident, init_db

def verify_rag():
    print("--- Starting RAG Verification ---")

    # 1. Initialize DB
    init_db()

    # 2. Add a unique test incident
    unique_id = str(uuid.uuid4())[:8]
    test_title = f"Test Incident {unique_id}"
    test_desc = "The flux capacitor is overheating due to 1.21 gigawatts overload."

    db = SessionLocal()
    try:
        new_inc = Incident(
            id=unique_id,
            title=test_title,
            severity="SEV-1",
            description=test_desc,
            status="RESOLVED",
            updates='["Initial investigation started."]'
        )
        db.add(new_inc)
        db.commit()
        print(f"Created test incident: {test_title}")
    finally:
        db.close()

    # 3. Initialize RAG (should index the new incident)
    initialize_rag()

    # 4. Search for Runbook (from mock data)
    print("\nSearch 1: 'restart service'")
    results_runbook = rag_engine.search("restart service")
    found_runbook = False
    for doc in results_runbook:
        print(f" - Found: {doc.page_content[:50]}... (Type: {doc.metadata.get('type')})")
        if doc.metadata.get('type') == 'runbook' and 'restart_service' in doc.metadata.get('name', ''):
            found_runbook = True

    if found_runbook:
        print("✅ Runbook verification PASSED")
    else:
        print("❌ Runbook verification FAILED")

    # 5. Search for the Incident
    print(f"\nSearch 2: 'flux capacitor overload'")
    results_inc = rag_engine.search("flux capacitor overload")
    found_inc = False
    for doc in results_inc:
        print(f" - Found: {doc.page_content[:50]}... (Type: {doc.metadata.get('type')})")
        if doc.metadata.get('type') == 'incident' and doc.metadata.get('id') == unique_id:
            found_inc = True

    if found_inc:
        print("✅ Incident verification PASSED")
    else:
        print("❌ Incident verification FAILED")

    if found_runbook and found_inc:
        print("\n🎉 ALL RAG CHECKS PASSED")
    else:
        print("\n💥 RAG CHECKS FAILED")
        sys.exit(1)

if __name__ == "__main__":
    verify_rag()
