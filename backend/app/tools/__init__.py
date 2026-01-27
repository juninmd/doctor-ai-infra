import os

if os.getenv("USE_REAL_TOOLS", "true").lower() == "true":
    from .real import (
        list_k8s_pods, describe_pod,
        check_gcp_status, query_gmp_prometheus,
        get_datadog_metrics, check_azion_edge,
        check_github_repos, get_pr_status,
        check_pipeline_status, get_argocd_sync_status,
        check_vulnerabilities, analyze_iam_policy
    )
else:
    from .mocks import (
        list_k8s_pods, describe_pod,
        check_gcp_status, query_gmp_prometheus,
        get_datadog_metrics, check_azion_edge,
        check_github_repos, get_pr_status,
        check_pipeline_status, get_argocd_sync_status,
        check_vulnerabilities, analyze_iam_policy
    )
