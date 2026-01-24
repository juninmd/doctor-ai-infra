from typing import Literal
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import create_react_agent

from .llm import get_llm
from .tools import list_k8s_pods, describe_pod, check_gcp_status, query_gmp_prometheus, get_datadog_metrics, check_azion_edge
from .state import AgentState

# 1. Initialize LLM
llm = get_llm()

# 2. Define Tools for each specialist
k8s_tools = [list_k8s_pods, describe_pod]
gcp_tools = [check_gcp_status, query_gmp_prometheus]
datadog_tools = [get_datadog_metrics]
azion_tools = [check_azion_edge]

# 3. Create Specialist Agents (using prebuilt ReAct agent for simplicity)
# We add a system message to give them personality
def make_specialist(tools, persona):
    system_msg = f"""You are a specialist in {persona}.
    Analyze the situation using your tools.
    Your tone is relaxed, direct, and technical but friendly.
    Do not use stiff corporate language. Just solve the problem.
    """
    return create_react_agent(llm, tools, prompt=system_msg)

k8s_agent = make_specialist(k8s_tools, "Kubernetes (K8s)")
gcp_agent = make_specialist(gcp_tools, "Google Cloud Platform (GCP)")
datadog_agent = make_specialist(datadog_tools, "Datadog Monitoring")
azion_agent = make_specialist(azion_tools, "Azion Edge Computing")

# 4. Define the Supervisor (Router)
# The supervisor decides which agent to call or to finish.
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# Ideally we use function calling for routing, but with Ollama generic,
# sometimes structured output is better handled via simple prompt if tools aren't perfect.
# But let's try the Tool/Function calling approach first as it's cleaner.
# We will create a "Supervisor" that has access to a "function" for each worker.

members = ["K8s_Specialist", "GCP_Specialist", "Datadog_Specialist", "Azion_Specialist"]
options = ["FINISH"] + members

system_prompt = (
    "You are a supervisor tasked with managing a conversation between the"
    " following workers: {members}. Given the following user request,"
    " respond with the worker to act next. Each worker will perform a"
    " task and respond with their results and status. When finished,"
    " respond with FINISH."
    " NOTE: If a worker reports an error involving another service (e.g., K8s logs show a DB error),"
    " you MUST call the relevant specialist (e.g., GCP_Specialist for Cloud SQL) to investigate."
    " Maintain a relaxed and direct tone in your internal thought process."
)

# Using a simpler routing logic for robustness with smaller local models
def supervisor_node(state: AgentState):
    messages = state["messages"]
    last_message = messages[-1]

    # Simple keyword based routing as a fallback/robustness for this demo
    # if the LLM isn't smart enough without fine-tuning.
    # However, we will try to ask the LLM.

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages"),
        ("system", "Given the conversation above, who should act next? Select one of: {options}. Return ONLY the name of the option."),
    ]).partial(options=str(options), members=", ".join(members))

    chain = prompt | llm
    response = chain.invoke(messages)
    decision = response.content.strip()

    # Cleaning up response just in case
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

workflow.add_edge(START, "Supervisor")

for member in members:
    workflow.add_edge(member, "Supervisor")

# Conditional edges from Supervisor
workflow.add_conditional_edges(
    "Supervisor",
    lambda x: x["next"],
    {
        "K8s_Specialist": "K8s_Specialist",
        "GCP_Specialist": "GCP_Specialist",
        "Datadog_Specialist": "Datadog_Specialist",
        "Azion_Specialist": "Azion_Specialist",
        "FINISH": END
    }
)

app_graph = workflow.compile()
