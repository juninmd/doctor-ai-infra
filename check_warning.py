from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from app.llm import get_llm
import warnings

# Filter to see only our specific warning
warnings.simplefilter('always')

@tool
def magic(x: int) -> int:
    """Adds 1 to x."""
    return x + 1

try:
    llm = get_llm()
    graph = create_react_agent(llm, [magic], prompt="You are a wizard.")
    print("Graph created successfully")
except Exception as e:
    print(f"Error: {e}")
