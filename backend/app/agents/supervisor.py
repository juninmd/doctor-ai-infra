import operator
from typing import Annotated, List, Sequence, TypedDict, Union

from langchain_core.messages import BaseMessage, FunctionMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import BaseTool
from langchain.agents import create_openai_tools_agent
from langgraph.graph import StateGraph, END

from app.llm import get_llm
from app.tools.mocks import list_pods, describe_pod, check_vm_status, get_dd_metrics, check_azion_edge_function

# Define the state
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next_agent: str

# Define tools for each agent
k8s_tools = [list_pods, describe_pod]
gcp_tools = [check_vm_status]
datadog_tools = [get_dd_metrics]
azion_tools = [check_azion_edge_function]

# Helper to create an agent node
def create_agent(llm, tools, system_prompt):
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    # create_openai_tools_agent is the correct function for this version.
    agent = create_openai_tools_agent(llm, tools, prompt)
    from langchain.agents import AgentExecutor
    executor = AgentExecutor(agent=agent, tools=tools)
    return executor

def agent_node(state, agent, name):
    result = agent.invoke(state)
    return {"messages": [HumanMessage(content=result["output"], name=name)]}

# Supervisor Agent
def supervisor_node(state):
    llm = get_llm()

    system_prompt = (
        "You are a cool, relaxed, and direct Infrastructure Supervisor Agent. "
        "You manage a team of specialists: [K8sAgent, GCPAgent, DatadogAgent, AzionAgent]. "
        "Don't be stiff. Get straight to the point. Use casual language but remain professional enough to get the job done. "
        "Given the user request, decide who should act next. "
        "Respond with just the name of the worker to act next, or FINISH if the task is done."
    )

    options = ["K8sAgent", "GCPAgent", "DatadogAgent", "AzionAgent"]

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages"),
        (
            "system",
            "Given the conversation above, who should act next?"
            " Or should we FINISH? Select one of: {options}",
        ),
    ]).partial(options=str(options), team_members=", ".join(options))

    chain = prompt | llm

    result = chain.invoke(state)
    content = result.content.strip()

    if "K8sAgent" in content:
        next_agent = "K8sAgent"
    elif "GCPAgent" in content:
        next_agent = "GCPAgent"
    elif "DatadogAgent" in content:
        next_agent = "DatadogAgent"
    elif "AzionAgent" in content:
        next_agent = "AzionAgent"
    else:
        next_agent = "FINISH"

    return {"next_agent": next_agent}


# Build the Graph
def build_graph():
    llm = get_llm()

    k8s_agent = create_agent(llm, k8s_tools, "You are a relaxed K8s Specialist. You check clusters. Be brief and direct.")
    gcp_agent = create_agent(llm, gcp_tools, "You are a chill GCP Specialist. You check Cloud stuff. Keep it short.")
    dd_agent = create_agent(llm, datadog_tools, "You are a Datadog Specialist. You check metrics. Straight to the data.")
    azion_agent = create_agent(llm, azion_tools, "You are an Azion Specialist. You check edge resources. No fluff.")

    workflow = StateGraph(AgentState)

    workflow.add_node("Supervisor", supervisor_node)
    workflow.add_node("K8sAgent", lambda state: agent_node(state, k8s_agent, "K8sAgent"))
    workflow.add_node("GCPAgent", lambda state: agent_node(state, gcp_agent, "GCPAgent"))
    workflow.add_node("DatadogAgent", lambda state: agent_node(state, dd_agent, "DatadogAgent"))
    workflow.add_node("AzionAgent", lambda state: agent_node(state, azion_agent, "AzionAgent"))

    workflow.set_entry_point("Supervisor")

    # Conditional edges from Supervisor
    workflow.add_conditional_edges(
        "Supervisor",
        lambda x: x["next_agent"],
        {
            "K8sAgent": "K8sAgent",
            "GCPAgent": "GCPAgent",
            "DatadogAgent": "DatadogAgent",
            "AzionAgent": "AzionAgent",
            "FINISH": END
        }
    )

    # Edges from agents back to Supervisor
    workflow.add_edge("K8sAgent", "Supervisor")
    workflow.add_edge("GCPAgent", "Supervisor")
    workflow.add_edge("DatadogAgent", "Supervisor")
    workflow.add_edge("AzionAgent", "Supervisor")

    return workflow.compile()
