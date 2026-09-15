import operator
from typing import Annotated, Sequence, TypedDict, Union  # noqa
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str
