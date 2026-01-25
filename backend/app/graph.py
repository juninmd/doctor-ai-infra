from typing import Literal
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from .llm import get_llm
from .tools import (
    list_k8s_pods, describe_pod,
    check_gcp_status, query_gmp_prometheus,
    get_datadog_metrics, check_azion_edge,
    check_github_repos, get_pr_status,
    check_pipeline_status, get_argocd_sync_status,
    check_vulnerabilities, analyze_iam_policy
)
from .state import AgentState

# 1. Initialize LLM
llm = get_llm()

# 2. Define Tools for each specialist
k8s_tools = [list_k8s_pods, describe_pod]
gcp_tools = [check_gcp_status, query_gmp_prometheus]
datadog_tools = [get_datadog_metrics]
azion_tools = [check_azion_edge]
git_tools = [check_github_repos, get_pr_status]
cicd_tools = [check_pipeline_status, get_argocd_sync_status]
sec_tools = [check_vulnerabilities, analyze_iam_policy]


# 3. Create Specialist Agents
def make_specialist(tools, persona):
    system_msg = (
        f"You are a top-tier Infrastructure Specialist focusing on {{persona}}.\n"
        "Your goal is to troubleshoot issues efficiently and proactively.\n"
        "Use your tools immediately to gather data. Do not guess.\n"
        "If you see an error related to another domain, mention it clearly so the Supervisor can route it.\n"
        "Your tone is relaxed, direct, and technical (hacker-chic, not corporate).\n"
        "Current Year: 2026.\n"
    ).format(persona=persona)

    return create_react_agent(llm, tools, prompt=system_msg)

k8s_agent = make_specialist(k8s_tools, "Kubernetes (K8s) & Container Orchestration")
gcp_agent = make_specialist(gcp_tools, "Google Cloud Platform (GCP) & Cloud Infrastructure")
datadog_agent = make_specialist(datadog_tools, "Datadog Observability & Metrics")
azion_agent = make_specialist(azion_tools, "Azion Edge Computing & CDNs")
git_agent = make_specialist(git_tools, "Git, GitHub & Source Code Management")
cicd_agent = make_specialist(cicd_tools, "CI/CD Pipelines & ArgoCD")
sec_agent = make_specialist(sec_tools, "DevSecOps, Vulnerability Scanning & IAM")

# 4. Define the Supervisor (Router)
members = [
    "K8s_Specialist",
    "GCP_Specialist",
    "Datadog_Specialist",
    "Azion_Specialist",
    "Git_Specialist",
    "CICD_Specialist",
    "Security_Specialist"
]
options = ["FINISH"] + members

supervisor_system_prompt = (
    "You are the Supervisor Agent of a futuristic (2026) DevOps & Infrastructure Operations Team.\n"
    "Your team consists of: {members}.\n"
    "Your job is to orchestrate the troubleshooting session from Code to Deploy.\n"
    "1. Analyze the user's request or the previous agent's findings.\n"
    "2. Decide which specialist is best suited to take the NEXT step.\n"
    "   - Issues with pods/clusters -> K8s_Specialist\n"
    "   - Issues with Cloud/VMs -> GCP_Specialist\n"
    "   - Metrics/Alerts -> Datadog_Specialist\n"
    "   - Edge/CDN -> Azion_Specialist\n"
    "   - Repos/PRs/Code -> Git_Specialist\n"
    "   - Builds/Pipelines/ArgoCD -> CICD_Specialist\n"
    "   - Vulnerabilities/IAM -> Security_Specialist\n"
    "3. If a specialist reports an error in another domain (e.g. CI failed, check code), "
    "IMMEDIATELY route to the specialist for that domain.\n"
    "4. If the issue is resolved or you have a final answer, respond with FINISH.\n"
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
        "FINISH": END
    }
)

app_graph = workflow.compile()
