import pytest
import os
from app.tools.mocks import optimize_k8s_resources as mock_optimize
from app.tools.k8s_optimizer import optimize_k8s_resources as real_optimize

def test_mock_optimization():
    result = mock_optimize.invoke({"namespace": "default"})
    assert "🚀 [MOCK] K8s Resource Optimization Report" in result
    assert "frontend-web" in result
    assert "payment-api" in result

def test_real_optimization_client_unavailable():
    # Test that it handles missing k8s client gracefully when not in a cluster
    # We force the env var to true if it's not set, but here we just want to see if it handles errors
    result = real_optimize.invoke({"namespace": "default"})
    # Since we are running in a dev environment without a k8s cluster configured,
    # it should return an error message rather than crashing.
    assert "Error" in result or "K8s Resource Optimization Report" in result
