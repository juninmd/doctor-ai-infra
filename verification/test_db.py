import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.db import init_db, SessionLocal, Incident
import uuid

def test_db():
    print("Initializing DB...")
    init_db()

    db = SessionLocal()
    try:
        inc_id = str(uuid.uuid4())[:8]
        inc = Incident(
            id=inc_id,
            title="Test Incident",
            severity="SEV-3",
            description="This is a test."
        )
        db.add(inc)
        db.commit()
        print(f"Created incident {inc_id}")

        # Read back
        read_inc = db.query(Incident).filter(Incident.id == inc_id).first()
        if read_inc:
            print(f"Read back incident: {read_inc.title}")
            read_inc.add_update("Update 1")
            db.commit()
            print("Added update.")
        else:
            print("Failed to read back incident.")
            exit(1)

    finally:
        db.close()
        # Cleanup
        if os.path.exists("sre_agent.db"):
            os.remove("sre_agent.db")
            print("Cleaned up DB file.")

if __name__ == "__main__":
    test_db()
