
import os
import sys

# Ensure backend module is in path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# Force mock tools for safe verification
os.environ["USE_REAL_TOOLS"] = "false"

from backend.app.tools import (
    get_pod_logs,
    get_cluster_events,
    list_compute_instances,
    get_gcp_sql_instances,
    get_active_alerts
)

def test_tools_existence():
    print("Verifying tool imports...")
    print(f"DEBUG: get_pod_logs type: {type(get_pod_logs)}")
    print(f"DEBUG: get_pod_logs dir: {dir(get_pod_logs)}")
    # LangChain tools might wrap the function. Check if it has 'invoke'
    if hasattr(get_pod_logs, "invoke"):
        print("DEBUG: get_pod_logs has invoke method.")

    assert callable(get_pod_logs) or hasattr(get_pod_logs, "invoke"), "get_pod_logs is not callable/invokable"
    assert callable(get_cluster_events) or hasattr(get_cluster_events, "invoke"), "get_cluster_events is not callable"
    assert callable(list_compute_instances) or hasattr(list_compute_instances, "invoke"), "list_compute_instances is not callable"
    assert callable(get_gcp_sql_instances) or hasattr(get_gcp_sql_instances, "invoke"), "get_gcp_sql_instances is not callable"
    assert callable(get_active_alerts) or hasattr(get_active_alerts, "invoke"), "get_active_alerts is not callable"
    print("✅ All new tools imported successfully.")

def test_mock_execution():
    print("Verifying mock execution...")

    # Test K8s Logs
    logs = get_pod_logs.invoke({"pod_name": "frontend-123"})
    assert "ConnectionRefusedError" in logs
    print(f"✅ get_pod_logs returned: {logs[:50]}...")

    # Test K8s Events
    events = get_cluster_events.invoke({"namespace": "default"})
    assert "Back-off" in events
    print(f"✅ get_cluster_events returned: {events[:50]}...")

    # Test GCP Compute
    vms = list_compute_instances.invoke({"zone": "us-west1-b"})
    assert "web-server-1" in vms
    print(f"✅ list_compute_instances returned: {vms[:50]}...")

    # Test GCP SQL
    dbs = get_gcp_sql_instances.invoke({})
    assert "postgres-db" in dbs
    print(f"✅ get_gcp_sql_instances returned: {dbs[:50]}...")

    # Test Datadog Alerts
    alerts = get_active_alerts.invoke({"tags": "payment"})
    assert "Payment API" in alerts
    print(f"✅ get_active_alerts returned: {alerts[:50]}...")

if __name__ == "__main__":
    try:
        test_tools_existence()
        test_mock_execution()
        print("\n🎉 Verification Successful!")
    except Exception as e:
        print(f"\n❌ Verification Failed: {str(e)}")
        sys.exit(1)
