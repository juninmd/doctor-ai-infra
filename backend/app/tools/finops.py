from langchain_core.tools import tool
import json
import random
from datetime import datetime, timedelta, UTC

@tool
def analyze_cost_anomalies(days: int = 7) -> str:
    """
    Analyzes cloud billing data to detect sudden spikes or cost anomalies.
    Uses AI to identify which service caused the spike and why.
    """
    # In a real environment, this queries GCP Billing API or Datadog Cost Management
    spikes = [
        {"service": "Cloud SQL", "spike_pct": "+45%", "cause": "Unoptimized heavy queries causing auto-scaling of IOPS."},
        {"service": "Network Egress", "spike_pct": "+120%", "cause": "New frontend deployment caching misconfiguration (Azion Edge bypass)."}
    ]
    
    report = [f"### 💸 FinOps Cost Anomaly Report (Last {days} Days)"]
    for s in spikes:
        report.append(f"- **🚨 {s['service']}**: {s['spike_pct']} spike. \n  *Root Cause*: {s['cause']}")
        
    report.append("\n**Recommendation**: Route to Azion_Specialist to fix cache bypass, and Code_Specialist to review SQL queries.")
    return "\n".join(report)

@tool
def suggest_spot_migrations(namespace: str = "default") -> str:
    """
    Identifies stateless, fault-tolerant workloads that can be migrated to cheaper Spot/Preemptible VMs.
    Analyzes deployment specs for replicas, HPA, and lack of persistent volumes.
    """
    # Mocking real K8s API checks for statelessness
    candidates = ["worker-queue-processor", "image-resizer-service", "batch-analytics-job"]
    
    report = [f"### 🎯 Spot Instance Migration Candidates (Namespace: {namespace})"]
    report.append("The following workloads are strictly stateless, use HPA, and have no persistent volumes. Moving them to Spot nodes can save ~70% of compute costs:")
    
    for c in candidates:
        report.append(f"- **{c}**: Estimated savings: $450/month.")
        
    report.append("\n**Action**: Run `execute_runbook` with 'migrate_to_spot_nodepool' to apply these changes.")
    return "\n".join(report)

@tool
def predict_resource_exhaustion() -> str:
    """
    Predictive Maintenance: Extrapolates current metric trends to predict future system outages (e.g., Disk Full, Memory Leaks).
    """
    # Mocking advanced time-series forecasting (ARIMA/Prophet)
    now = datetime.now(UTC)
    disk_full_date = now + timedelta(days=3, hours=4)
    mem_leak_date = now + timedelta(days=1, hours=12)
    
    report = ["### 🔮 Predictive Maintenance Forecast"]
    report.append(f"- ⚠️ **postgres-db-pv**: Disk usage trend indicates it will reach 100% capacity around **{disk_full_date.strftime('%Y-%m-%d %H:%M UTC')}** (in ~3 days).")
    report.append(f"- ⚠️ **payment-api**: Memory consumption is linearly increasing (+10MB/hr). OOMKill predicted around **{mem_leak_date.strftime('%Y-%m-%d %H:%M UTC')}**.")
    report.append("\n**Action**: Proactively resize PVC for 'postgres-db-pv' and restart 'payment-api' while investigating the leak.")
    
    return "\n".join(report)
