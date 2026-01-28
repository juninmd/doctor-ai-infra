import os

if os.getenv("USE_REAL_TOOLS", "true").lower() == "true":
    from .real import (
        list_k8s_pods, describe_pod, get_pod_logs, get_cluster_events,
        check_gcp_status, query_gmp_prometheus, list_compute_instances, get_gcp_sql_instances,
        get_datadog_metrics, get_active_alerts, check_azion_edge,
        check_github_repos, get_pr_status,
        check_pipeline_status, get_argocd_sync_status,
        check_vulnerabilities, analyze_iam_policy,
        analyze_log_patterns, diagnose_service_health, analyze_ci_failure, create_issue
    )
else:
    from .mocks import (
        list_k8s_pods, describe_pod, get_pod_logs, get_cluster_events,
        check_gcp_status, query_gmp_prometheus, list_compute_instances, get_gcp_sql_instances,
        get_datadog_metrics, get_active_alerts, check_azion_edge,
        check_github_repos, get_pr_status,
        check_pipeline_status, get_argocd_sync_status,
        check_vulnerabilities, analyze_iam_policy,
        analyze_log_patterns, diagnose_service_health, analyze_ci_failure, create_issue
    )
