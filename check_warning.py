import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app.agents.utils import create_agent
from langchain_core.tools import tool
from app.llm import get_llm
import warnings

# Filter to see only our specific warning
warnings.simplefilter('always')

@tool  # noqa: E302
def magic(x: int) -> int:
    """Adds 1 to x."""
    return x + 1

try:  # noqa: E305
    llm = get_llm()
    graph = create_agent(llm, [magic], system_prompt="You are a wizard.")
    print("Graph created successfully")
except Exception as e:
    print(f"Error: {e}")
