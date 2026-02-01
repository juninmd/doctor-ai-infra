import os
import sys

# Ensure we use mocks where applicable
os.environ["USE_REAL_TOOLS"] = "false"
# Add backend to path
sys.path.append(os.getcwd())

# Mock DB for incident tool
from app.db import init_db
init_db()

from app.tools.observability import investigate_root_cause
from app.tools.incident import suggest_remediation
# list_recent_commits might be in mocks or real depending on how __init__ resolved
# But we added it to both.
from app.tools import list_recent_commits

print("--- Verifying list_recent_commits ---")
try:
    res = list_recent_commits.invoke({"owner": "my-org", "repo": "backend-repo", "hours": 24})
    print(res)
except Exception as e:
    print(f"FAILED: {e}")

print("\n--- Verifying investigate_root_cause ---")
try:
    # This calls mocks internally
    res = investigate_root_cause.invoke({"service_name": "frontend", "time_window_minutes": 30})
    print(res)
except Exception as e:
    print(f"FAILED: {e}")

print("\n--- Verifying suggest_remediation ---")
try:
    # RAG might return empty if empty, but shouldn't crash
    res = suggest_remediation.invoke({"incident_context": "Database connection failed"})
    print(res)
except Exception as e:
    print(f"FAILED: {e}")

print("\nVerification Complete.")
