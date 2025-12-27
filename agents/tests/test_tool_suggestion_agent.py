# agents/tests/test_tool_suggestion_agent.py
import pytest
from unittest.mock import patch, MagicMock
from agents.tool_suggesting_agent import ToolSuggestionAgent

# ---------------- FIXTURES ---------------- #
@pytest.fixture
def mock_pipeline():
    with patch("agents.tool_suggesting_agent.ToolRetrievalPipeline") as MockPipeline:
        instance = MockPipeline.return_value
        instance.retrieve_tools.return_value = [{"id": "t1", "name": "ToolA", "category": "Bio"}]
        yield instance

@pytest.fixture
def mock_formatter():
    with patch("agents.tool_suggesting_agent.format_tool_results") as mock_format:
        mock_format.return_value = {"results": [{"id": "t1", "name": "ToolA", "category": "Bio", "score": 0.95}]}
        yield mock_format

# ---------------- CORE LOGIC TESTS ---------------- #
def test_suggest_tools_calls_pipeline_and_formatter(mock_pipeline, mock_formatter):
    neo_client = MagicMock()
    agent = ToolSuggestionAgent(neo_client=neo_client, top_k_default=5)

    # Patch pipeline & formatter
    agent.pipeline = mock_pipeline

    results = agent.suggest_tools("test query", top_k=3)

    # Check pipeline called correctly
    mock_pipeline.retrieve_tools.assert_called_once_with("test query", top_k=3)

    # Check formatter called correctly
    mock_formatter.assert_called_once_with(mock_pipeline.retrieve_tools.return_value, "test query")

    # Validate results structure
    assert isinstance(results, list)
    assert len(results) == 1
    tool = results[0]
    assert "id" in tool
    assert "name" in tool
    assert "category" in tool
    assert "score" in tool

def test_suggest_tools_default_topk(mock_pipeline, mock_formatter):
    neo_client = MagicMock()
    agent = ToolSuggestionAgent(neo_client=neo_client, top_k_default=5)
    agent.pipeline = mock_pipeline

    _ = agent.suggest_tools("another query")  # no top_k passed

    # Should use default top_k
    mock_pipeline.retrieve_tools.assert_called_once_with("another query", top_k=5)

def test_suggest_tools_empty_results(mock_pipeline, mock_formatter):
    neo_client = MagicMock()
    agent = ToolSuggestionAgent(neo_client=neo_client)
    agent.pipeline = mock_pipeline

    # Patch formatter to return empty list
    mock_formatter.return_value = {"results": []}
    results = agent.suggest_tools("query yielding no results", top_k=2)

    assert results == []