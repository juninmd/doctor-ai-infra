import pytest
from unittest.mock import MagicMock, patch
import os
import sys

# Ensure we are testing real tools logic (though we patch the heavy lifting)
from app.tools.real import trace_service_health
from app.db import Service, SessionLocal, init_db
from app.tools.runbooks import bootstrap_catalog

@pytest.fixture(scope="module")
def db_session():
    # Ensure DB is initialized
    init_db()
    # Bootstrap if empty
    bootstrap_catalog()

    db = SessionLocal()
    yield db
    db.close()

def test_trace_service_health_db_integration(db_session):
    # Ensure service exists
    service = db_session.query(Service).filter(Service.name == "payment-api").first()
    if not service:
        pytest.skip("payment-api service not found in DB")

    print(f"Service Found: {service.name} with deps: {[d.name for d in service.dependencies]}")

    # Patch diagnose_service_health inside app.tools.real
    with patch("app.tools.real.diagnose_service_health") as mock_tool:
        mock_tool.invoke.return_value = "Health Check: OK"

        # We need to ensure we call the function with the argument
        # invoke is called with {"service_name": ..., "namespace": ...}

        report = trace_service_health.invoke({"service_name": "payment-api", "depth": 1})

        print(report)

        assert "Root: payment-api" in report
        assert "Dependencies" in report

        # Check if dependencies are listed
        # payment-api depends on auth-service, fraud-detection, payment-db
        assert "auth-service" in report
        assert "fraud-detection" in report
        assert "payment-db" in report
