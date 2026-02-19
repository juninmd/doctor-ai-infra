import pytest
from unittest.mock import MagicMock, patch
import sys
from io import StringIO
from langchain_core.messages import AIMessage
from backend.cli import run_single_shot, run_interactive

@patch("backend.cli.app_graph")
def test_run_single_shot(mock_graph, capsys):
    # Setup mock stream
    mock_graph.stream.return_value = [
        {"Supervisor": {"next": "K8s_Specialist"}},
        {"K8s_Specialist": {"messages": [AIMessage(content="Checking pods...")]}}
    ]

    run_single_shot("status")

    captured = capsys.readouterr()
    assert "Processing: status" in captured.out
    assert "Routing to -> K8s_Specialist" in captured.out
    assert "Checking pods..." in captured.out

@patch("backend.cli.app_graph")
@patch("builtins.input", side_effect=["status", "exit"])
def test_run_interactive(mock_input, mock_graph, capsys):
    # Setup mock stream
    mock_graph.stream.return_value = [
        {"Supervisor": {"next": "Topology_Specialist"}}
    ]

    run_interactive()

    captured = capsys.readouterr()
    assert "SRE Agent CLI" in captured.out
    assert "Thinking..." in captured.out
    assert "Routing to -> Topology_Specialist" in captured.out
    assert "Goodbye!" in captured.out
