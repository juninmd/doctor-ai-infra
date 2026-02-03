import os

# New tool import
from .observability import investigate_root_cause, scan_infrastructure, analyze_heavy_logs

if os.getenv("USE_REAL_TOOLS", "true").lower() == "true":
    from .real import (
        list_k8s_pods, describe_pod, get_pod_logs, get_cluster_events,
        check_gcp_status, query_gmp_prometheus, list_compute_instances, get_gcp_sql_instances,
        get_datadog_metrics, get_active_alerts, check_azion_edge,
        check_github_repos, get_pr_status, list_recent_commits,
        check_pipeline_status, get_argocd_sync_status,
        check_vulnerabilities, analyze_iam_policy,
        analyze_log_patterns, diagnose_service_health, analyze_ci_failure, create_issue,
        trace_service_health, purge_azion_cache, diagnose_azion_configuration,
        list_datadog_metrics, check_on_call_schedule, send_slack_notification
    )
else:
    from .mocks import (
        list_k8s_pods, describe_pod, get_pod_logs, get_cluster_events,
        check_gcp_status, query_gmp_prometheus, list_compute_instances, get_gcp_sql_instances,
        get_datadog_metrics, get_active_alerts, check_azion_edge,
        check_github_repos, get_pr_status, list_recent_commits,
        check_pipeline_status, get_argocd_sync_status,
        check_vulnerabilities, analyze_iam_policy,
        analyze_log_patterns, diagnose_service_health, analyze_ci_failure, create_issue,
        trace_service_health, purge_azion_cache, diagnose_azion_configuration,
        list_datadog_metrics, check_on_call_schedule, send_slack_notification
    )
