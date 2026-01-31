import pytest
from app.db import init_db
from app.tools.runbooks import bootstrap_catalog

@pytest.fixture(scope="session", autouse=True)
def setup_db():
    """Initializes and bootstraps the database for the test session."""
    init_db()
    bootstrap_catalog()
