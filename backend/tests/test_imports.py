import os
import pytest

def test_imports_real():
    # Force use of real tools
    os.environ["USE_REAL_TOOLS"] = "true"
    try:
        from app.tools import real
        assert hasattr(real, "analyze_ci_failure"), "analyze_ci_failure missing in app.tools.real"
    except ImportError as e:
        pytest.fail(f"Failed to import app.tools.real: {e}")

def test_imports_init():
    # Test top level import
    try:
        from app.tools import analyze_ci_failure, check_traefik_health
        assert analyze_ci_failure is not None
        assert check_traefik_health is not None
    except ImportError as e:
        pytest.fail(f"Failed to import from app.tools: {e}")
