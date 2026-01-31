import os

# CI Tools are hybrid (mock/real inside the tool based on token)
from .ci import (
    check_github_repos, get_pr_status,
    check_pipeline_status, analyze_ci_failure, list_recent_builds
)

if os.getenv("USE_REAL_TOOLS", "true").lower() == "true":
    from .real import (
        list_k8s_pods, describe_pod, get_pod_logs, get_cluster_events,
        check_gcp_status, query_gmp_prometheus, list_compute_instances, get_gcp_sql_instances,
        get_datadog_metrics, get_active_alerts, check_azion_edge,
        # Github/CI tools moved to .ci
        get_argocd_sync_status,
        check_vulnerabilities, analyze_iam_policy,
        analyze_log_patterns, diagnose_service_health, analyze_ci_failure, create_issue,
        trace_service_health, purge_azion_cache
    )
else:
    from .mocks import (
        list_k8s_pods, describe_pod, get_pod_logs, get_cluster_events,
        check_gcp_status, query_gmp_prometheus, list_compute_instances, get_gcp_sql_instances,
        get_datadog_metrics, get_active_alerts, check_azion_edge,
        # Github/CI tools moved to .ci (mocks.py versions ignored in favor of ci.py)
        get_argocd_sync_status,
        check_vulnerabilities, analyze_iam_policy,
        analyze_log_patterns, diagnose_service_health, analyze_ci_failure, create_issue,
        trace_service_health, purge_azion_cache
    )
