# tests/test_tool_graph_context.py

import pytest
from unittest.mock import MagicMock
from agents.graphRAG.retrieval.tool_graph_context import ToolGraphContext


@pytest.fixture
def mock_neo_client():
    """Return a mocked Neo4j client."""
    return MagicMock()


def test_get_tool_context_returns_results(mock_neo_client):
    # Arrange
    mock_neo_client.run_query.return_value = [
        {
            "tool": {"tool_id": "tool_1", "name": "Tool One", "embedding": [0.1, 0.2]},
            "inputs": [{"name": "input_1"}],
            "outputs": [{"name": "output_1"}],
        }
    ]
    context = ToolGraphContext(mock_neo_client)
    tool_ids = ["tool_1"]

    # Act
    results = context.get_tool_context(tool_ids)

    # Assert
    assert len(results) == 1
    tool = results[0]["tool"]
    assert tool["tool_id"] == "tool_1"
    assert "embedding" not in tool  # _clean removed embedding
    assert results[0]["inputs"] == [{"name": "input_1"}]
    assert results[0]["outputs"] == [{"name": "output_1"}]
    mock_neo_client.run_query.assert_called_once()


def test_get_tool_context_empty_tool_ids(mock_neo_client, caplog):
    context = ToolGraphContext(mock_neo_client)
    with caplog.at_level("WARNING"):
        results = context.get_tool_context([])
    assert results == []
    assert "Empty tool_ids provided" in caplog.text


def test_get_tool_context_exception_returns_empty(mock_neo_client, caplog):
    mock_neo_client.run_query.side_effect = Exception("DB error")
    context = ToolGraphContext(mock_neo_client)
    tool_ids = ["tool_1"]

    with caplog.at_level("ERROR"):
        results = context.get_tool_context(tool_ids)

    assert results == []
    assert "Failed to retrieve tool context" in caplog.text


def test_clean_method_removes_embedding():
    node = {"tool_id": "t1", "embedding": [0.1, 0.2], "name": "Tool"}
    clean_node = ToolGraphContext._clean(node)
    assert "embedding" not in clean_node
    assert clean_node["tool_id"] == "t1"
    assert clean_node["name"] == "Tool"

    # Test with None
    assert ToolGraphContext._clean(None) == {}
