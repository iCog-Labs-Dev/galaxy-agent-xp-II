# agents/tests/test_workflow_suggestion_agent.py
import pytest
from unittest.mock import MagicMock, patch
from agents.workflow_suggestion_agent import WorkflowSuggestionAgent

# ---------------- FIXTURES ---------------- #
@pytest.fixture
def mock_pipeline():
    with patch("agents.workflow_suggestion_agent.WorkflowRetrievalPipeline") as MockPipeline:
        instance = MockPipeline.return_value
        instance.retrieve_workflows.return_value = [
            {"workflow_repository": "wf1", "category": "Bioinformatics", "readme_cleaned": "Desc1", "tool_names": ["ToolA"]},
            {"workflow_repository": "wf2", "category": "Chemistry", "readme_cleaned": "Desc2", "tool_names": ["ToolB"]}
        ]
        yield instance

@pytest.fixture
def mock_formatter():
    with patch("agents.workflow_suggestion_agent.format_workflow_results") as mock_format:
        mock_format.return_value = {
            "results": [
                {"name": "wf1", "category": "Bioinformatics", "score": 0.95, "readme_excerpt": "Desc1"},
                {"name": "wf2", "category": "Chemistry", "score": 0.90, "readme_excerpt": "Desc2"}
            ]
        }
        yield mock_format

# ---------------- CORE LOGIC TESTS ---------------- #
def test_suggest_workflows_calls_pipeline_and_formatter(mock_pipeline, mock_formatter):
    neo_client = MagicMock()
    agent = WorkflowSuggestionAgent(neo_client=neo_client, top_k_default=5)
    agent.pipeline = mock_pipeline

    results = agent.suggest_workflows("analyze genome", top_k=2)

    # Check pipeline called with correct args
    mock_pipeline.retrieve_workflows.assert_called_once_with("analyze genome", top_k=2)

    # Check formatter called with pipeline output
    mock_formatter.assert_called_once_with(mock_pipeline.retrieve_workflows.return_value, "analyze genome")

    # Validate results structure
    assert isinstance(results, list)
    assert len(results) == 2
    for wf in results:
        assert "name" in wf
        assert "category" in wf
        assert "score" in wf
        assert "readme_excerpt" in wf

def test_suggest_workflows_default_topk(mock_pipeline, mock_formatter):
    neo_client = MagicMock()
    agent = WorkflowSuggestionAgent(neo_client=neo_client, top_k_default=5)
    agent.pipeline = mock_pipeline

    _ = agent.suggest_workflows("default topk query")

    # Should use default top_k
    mock_pipeline.retrieve_workflows.assert_called_once_with("default topk query", top_k=5)

def test_suggest_workflows_empty_results(mock_pipeline, mock_formatter):
    neo_client = MagicMock()
    agent = WorkflowSuggestionAgent(neo_client=neo_client)
    agent.pipeline = mock_pipeline

    # Patch formatter to return empty list
    mock_formatter.return_value = {"results": []}
    results = agent.suggest_workflows("query with no results", top_k=2)

    assert results == []
