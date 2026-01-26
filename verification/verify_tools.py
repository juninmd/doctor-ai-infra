import os
import sys

# Set env var to trigger real tools import
os.environ["USE_REAL_TOOLS"] = "true"

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

try:
    from app.tools import list_k8s_pods, check_gcp_status, get_datadog_metrics, check_azion_edge
    print("SUCCESS: Successfully imported real tools.")
    print(f"list_k8s_pods: {list_k8s_pods.name}")
except ImportError as e:
    print(f"FAILURE: ImportError during verification: {e}")
    sys.exit(1)
except Exception as e:
    print(f"FAILURE: Exception during verification: {e}")
    sys.exit(1)
