import pytest
from app.tools.visualizer import generate_topology_diagram

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
