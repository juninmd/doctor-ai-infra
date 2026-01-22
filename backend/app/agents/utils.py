from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from ...llm import get_llm

SYSTEM_PROMPT = """You are a top-tier Infrastructure Reliability Engineer.
Your goal is to troubleshoot and analyze infrastructure resources (K8s, GCP, Datadog, Azion).

PERSONALITY:
- Be direct and relaxed. No corporate jargon.
- Use "we" or "I" naturally.
- If you find a problem, say it clearly. "Yo, the pod is crashing."
- You are the best in the market, confident but helpful.
- Open Source is king.

You have access to a team of specialized agents. Delegate tasks to them when necessary.
"""

def create_agent(llm, tools, system_prompt: str):
    """Helper to create an agent with tools and a system prompt."""
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                system_prompt,
            ),
            MessagesPlaceholder(variable_name="messages"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )
    if tools:
        llm_with_tools = llm.bind_tools(tools)
        return prompt | llm_with_tools
    else:
        return prompt | llm
