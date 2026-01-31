from typing import Literal
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from .llm import get_llm
from .tools import (
    list_k8s_pods, describe_pod, get_pod_logs, get_cluster_events,
    check_gcp_status, query_gmp_prometheus, list_compute_instances, get_gcp_sql_instances,
    get_datadog_metrics, get_active_alerts, check_azion_edge,
    check_github_repos, get_pr_status,
    check_pipeline_status, get_argocd_sync_status,
    check_vulnerabilities, analyze_iam_policy,
    analyze_log_patterns, diagnose_service_health, analyze_ci_failure, create_issue,
    trace_service_health, purge_azion_cache
)
from .tools.dashboard import analyze_infrastructure_health
from .tools.incident import (
    create_incident, update_incident_status, list_incidents, get_incident_details,
    generate_postmortem, log_incident_event, build_incident_timeline, manage_incident_channels
)
from .tools.runbooks import list_runbooks, execute_runbook, lookup_service, get_service_dependencies, get_service_topology
from .tools.visualizer import generate_topology_diagram
from .tools.knowledge import search_knowledge_base
from .state import AgentState

# 1. Initialize LLM
llm = get_llm()

# 2. Define Tools for each specialist
k8s_tools = [list_k8s_pods, describe_pod, get_pod_logs, get_cluster_events, analyze_log_patterns, diagnose_service_health, trace_service_health]
gcp_tools = [check_gcp_status, query_gmp_prometheus, list_compute_instances, get_gcp_sql_instances]
datadog_tools = [get_datadog_metrics, get_active_alerts]
azion_tools = [check_azion_edge, purge_azion_cache]
git_tools = [check_github_repos, get_pr_status]
cicd_tools = [check_pipeline_status, get_argocd_sync_status, analyze_ci_failure]
sec_tools = [check_vulnerabilities, analyze_iam_policy]
incident_tools = [
    create_incident, update_incident_status, list_incidents, get_incident_details,
    generate_postmortem, search_knowledge_base, create_issue,
    log_incident_event, build_incident_timeline, manage_incident_channels
]
automation_tools = [list_runbooks, execute_runbook, lookup_service]
topology_tools = [
    get_service_dependencies, get_service_topology, lookup_service,
    generate_topology_diagram, trace_service_health, analyze_infrastructure_health
]

# 3. Create Specialist Agents
def make_specialist(tools, persona, heuristics=""):
    system_msg = (
        f"You are a top-tier Infrastructure Specialist focusing on {{persona}}.\n"
        "Your goal is to troubleshoot issues efficiently and proactively.\n"
        "Use your tools immediately to gather data. Do not guess.\n"
        "If you see an error related to another domain, mention it clearly so the Supervisor can route it.\n"
        "Your tone is relaxed, direct, and technical (hacker-chic, not corporate).\n"
        "Current Year: 2026.\n"
        f"{{heuristics}}\n"
    ).format(persona=persona, heuristics=heuristics)

    return create_react_agent(llm, tools, prompt=system_msg)

k8s_agent = make_specialist(
    k8s_tools,
    "Kubernetes (K8s) & Container Orchestration",
    heuristics="SRE TIP: Start by calling `diagnose_service_health` for a full picture. If a pod is crashing, `analyze_log_patterns` is more efficient than reading raw logs. Use `trace_service_health` to check dependencies if the issue seems external."
)
gcp_agent = make_specialist(
    gcp_tools,
    "Google Cloud Platform (GCP) & Cloud Infrastructure",
    heuristics="SRE TIP: If a service is down or unreachable, check `check_gcp_status` for maintenance windows or outages first."
)
datadog_agent = make_specialist(
    datadog_tools,
    "Datadog Observability & Metrics",
    heuristics="SRE TIP: Correlate high latency spikes with error logs. Check for recent alerts."
)
azion_agent = make_specialist(azion_tools, "Azion Edge Computing & CDNs")
git_agent = make_specialist(git_tools, "Git, GitHub & Source Code Management")
cicd_agent = make_specialist(cicd_tools, "CI/CD Pipelines & ArgoCD")
sec_agent = make_specialist(sec_tools, "DevSecOps, Vulnerability Scanning & IAM")
incident_agent = make_specialist(
    incident_tools,
    "Incident Management & Post-Mortems",
    heuristics=(
        "SRE TIP: You are the Incident Commander. \n"
        "1. Create a channel with `manage_incident_channels`.\n"
        "2. Use `log_incident_event` to record your Hypotheses, Evidence, and Actions in real-time. This builds the timeline.\n"
        "3. Use `build_incident_timeline` to summarize the state for the user.\n"
        "4. Always act on facts, not assumptions."
    )
)
automation_agent = make_specialist(automation_tools, "Runbook Automation & Site Reliability Engineering")
topology_agent = make_specialist(
    topology_tools,
    "Service Topology & Dependency Mapping",
    heuristics=(
        "SRE TIP: You hold the map of the entire system.\n"
        "Use `analyze_infrastructure_health` to provide a global status report when asked about general health.\n"
        "Use `trace_service_health` to visualize cascading failures across the stack.\n"
        "Use `generate_topology_diagram` for architectural overviews."
    )
)

# 4. Define the Supervisor (Router)
members = [
    "K8s_Specialist",
    "GCP_Specialist",
    "Datadog_Specialist",
    "Azion_Specialist",
    "Git_Specialist",
    "CICD_Specialist",
    "Security_Specialist",
    "Incident_Specialist",
    "Automation_Specialist",
    "Topology_Specialist"
]
options = ["FINISH"] + members

supervisor_system_prompt = (
    "You are the Supervisor Agent of a futuristic (2026) DevOps & Infrastructure Operations Team.\n"
    "Your team consists of: {members}.\n"
    "Your job is to orchestrate the troubleshooting session from Code to Deploy.\n"
    "If the user speaks Portuguese, reply in Portuguese.\n"
    "1. Analyze the user's request or the previous agent's findings.\n"
    "2. Decide which specialist is best suited to take the NEXT step.\n"
    "   - General Status / Dashboard / 'How is the system?' / 'Troubleshoot' (no specific target) -> Topology_Specialist\n"
    "   - Issues with pods/clusters -> K8s_Specialist\n"
    "   - Issues with Cloud/VMs -> GCP_Specialist\n"
    "   - Metrics/Alerts -> Datadog_Specialist\n"
    "   - Edge/CDN -> Azion_Specialist\n"
    "   - Repos/PRs/Code -> Git_Specialist\n"
    "   - Builds/Pipelines/ArgoCD -> CICD_Specialist\n"
    "   - Vulnerabilities/IAM -> Security_Specialist\n"
    "   - Incidents/Outages/Status updates/Post-Mortems -> Incident_Specialist\n"
    "   - Runbooks/Remediation/Scripts -> Automation_Specialist\n"
    "   - Service Dependencies/Topology/Who calls what -> Topology_Specialist\n"
    "3. CRITICAL: If a specialist reports a dependency error (e.g. 'ConnectionRefused' or 'Database down'), "
    "IMMEDIATELY route to the specialist responsible for that dependency (e.g. GCP_Specialist for DBs) or Topology_Specialist to verify impact.\n"
    "4. Always summarize the key findings from the last agent before making the next move.\n"
    "5. If the issue is resolved or you have a final answer, respond with FINISH.\n"
    "Tone: Confident, relaxed, concise. No fluff."
)

def supervisor_node(state: AgentState):
    messages = state["messages"]

    prompt = ChatPromptTemplate.from_messages([
        ("system", supervisor_system_prompt),
        MessagesPlaceholder(variable_name="messages"),
        ("system", (
            "Who should act next? Select one of: {options}.\n"
            "Return ONLY the name of the option (e.g., 'K8s_Specialist').\n"
            "Do not add punctuation or explanation."
        )),
    ]).partial(options=str(options), members=", ".join(members))

    chain = prompt | llm
    response = chain.invoke(messages)
    decision = response.content.strip().replace(".", "").replace("'", "").replace('"', "")

    # Exact match check
    if decision in members:
        return {"next": decision}

    if "FINISH" in decision:
        return {"next": "FINISH"}

    # Fallback heuristic if LLM is chatty
    for member in members:
        if member in decision:
            return {"next": member}

    return {"next": "FINISH"}

# 5. Build the Graph
workflow = StateGraph(AgentState)

workflow.add_node("Supervisor", supervisor_node)
workflow.add_node("K8s_Specialist", k8s_agent)
workflow.add_node("GCP_Specialist", gcp_agent)
workflow.add_node("Datadog_Specialist", datadog_agent)
workflow.add_node("Azion_Specialist", azion_agent)
workflow.add_node("Git_Specialist", git_agent)
workflow.add_node("CICD_Specialist", cicd_agent)
workflow.add_node("Security_Specialist", sec_agent)
workflow.add_node("Incident_Specialist", incident_agent)
workflow.add_node("Automation_Specialist", automation_agent)
workflow.add_node("Topology_Specialist", topology_agent)

workflow.add_edge(START, "Supervisor")

for member in members:
    workflow.add_edge(member, "Supervisor")

workflow.add_conditional_edges(
    "Supervisor",
    lambda x: x["next"],
    {
        "K8s_Specialist": "K8s_Specialist",
        "GCP_Specialist": "GCP_Specialist",
        "Datadog_Specialist": "Datadog_Specialist",
        "Azion_Specialist": "Azion_Specialist",
        "Git_Specialist": "Git_Specialist",
        "CICD_Specialist": "CICD_Specialist",
        "Security_Specialist": "Security_Specialist",
        "Incident_Specialist": "Incident_Specialist",
        "Automation_Specialist": "Automation_Specialist",
        "Topology_Specialist": "Topology_Specialist",
        "FINISH": END
    }
)

app_graph = workflow.compile()
