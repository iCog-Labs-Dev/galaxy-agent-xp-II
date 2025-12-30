# tests/test_workflow_graph_context.py

import pytest
from unittest.mock import MagicMock
from retrieval.workflow_graph_context import WorkflowGraphContext


@pytest.fixture
def mock_neo_client():
    """Return a mocked Neo4j client."""
    return MagicMock()


def test_get_workflow_context_returns_results(mock_neo_client):
    # Arrange
    mock_neo_client.run_query.return_value = [
        {
            "workflow": {
                "workflow_id": "wf_1",
                "name": "Test Workflow",
                "readme": "README content",
                "download_url": "http://example.com",
            },
            "category": {"name": "Test Category"},
            "tools_used": ["ToolA", "ToolB"],
        }
    ]
    context = WorkflowGraphContext(mock_neo_client)
    workflow_ids = ["wf_1"]

    # Act
    results = context.get_workflow_context(workflow_ids)

    # Assert
    assert len(results) == 1
    assert results[0]["workflow"]["workflow_id"] == "wf_1"
    assert results[0]["category"]["name"] == "Test Category"
    assert results[0]["tools_used"] == ["ToolA", "ToolB"]
    mock_neo_client.run_query.assert_called_once()


def test_get_workflow_context_empty_workflow_ids(mock_neo_client, caplog):
    context = WorkflowGraphContext(mock_neo_client)
    
    with caplog.at_level("WARNING"):
        results = context.get_workflow_context([])

    assert results == []
    assert "Empty workflow_ids provided" in caplog.text


def test_get_workflow_context_exception_returns_empty(mock_neo_client, caplog):
    # Arrange: make run_query raise exception
    mock_neo_client.run_query.side_effect = Exception("DB error")
    context = WorkflowGraphContext(mock_neo_client)
    workflow_ids = ["wf_1"]

    # Act
    with caplog.at_level("ERROR"):
        results = context.get_workflow_context(workflow_ids)

    # Assert
    assert results == []
    assert "Failed to retrieve workflow context" in caplog.text