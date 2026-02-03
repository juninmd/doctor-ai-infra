import pytest
from sqlalchemy import event
from app.db import engine
from app.tools.visualizer import generate_topology_diagram

def test_topology_performance():
    """Ensure we don't regress to N+1 queries."""
    query_count = 0

    def count_queries(conn, cursor, statement, parameters, context, executemany):
        nonlocal query_count
        query_count += 1

    event.listen(engine, "before_cursor_execute", count_queries)
    try:
        generate_topology_diagram.invoke({"focus_service": "all"})
    finally:
        event.remove(engine, "before_cursor_execute", count_queries)

    # Should be 1 query (fetching services with joinedload).
    # Allowing a small buffer (e.g., < 5) in case of unexpected side queries,
    # but definitely not 20+.
    assert query_count < 5, f"Query count too high: {query_count}. Possible N+1 regression."

def test_generate_topology_diagram_all():
    result = generate_topology_diagram.invoke({"focus_service": "all"})
    assert "graph TD" in result
    assert "classDef" in result
    assert "payment-api" in result

def test_generate_topology_diagram_focus():
    result = generate_topology_diagram.invoke({"focus_service": "payment-api"})
    assert "graph TD" in result
    assert "payment-api" in result
    assert "auth-service" in result # Dependency
