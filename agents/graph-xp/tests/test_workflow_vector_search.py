# tests/test_workflow_vector_search.py

import pytest
import numpy as np
from unittest.mock import MagicMock
from retrieval.workflow_vector_search import WorkflowVectorSearch


@pytest.fixture
def mock_neo_client():
    """Return a mocked Neo4j client."""
    client = MagicMock()
    return client


def test_search_top_k_returns_results(mock_neo_client):
    # Arrange
    mock_neo_client.run_query.return_value = [
        {"workflow_id": "wf_1", "score": 0.95},
        {"workflow_id": "wf_2", "score": 0.90},
    ]
    search = WorkflowVectorSearch(mock_neo_client)
    query_embedding = np.random.rand(128)

    # Act
    results = search.search_top_k(query_embedding, top_k=2)

    # Assert
    assert len(results) == 2
    assert results[0] == ("wf_1", 0.95)
    assert results[1] == ("wf_2", 0.90)
    mock_neo_client.run_query.assert_called_once()


def test_search_top_k_invalid_embedding_type(mock_neo_client):
    search = WorkflowVectorSearch(mock_neo_client)
    with pytest.raises(ValueError, match="Query embedding must be a numpy ndarray"):
        search.search_top_k([1, 2, 3])  # not a numpy array


def test_search_top_k_invalid_embedding_dimension(mock_neo_client):
    search = WorkflowVectorSearch(mock_neo_client)
    query_embedding = np.random.rand(2, 2)  # 2D array
    with pytest.raises(ValueError, match="Query embedding must be 1-dimensional"):
        search.search_top_k(query_embedding)


def test_search_top_k_exception_returns_empty(mock_neo_client, caplog):
    # Arrange: make run_query raise exception
    mock_neo_client.run_query.side_effect = Exception("DB error")
    search = WorkflowVectorSearch(mock_neo_client)
    query_embedding = np.random.rand(128)

    # Act
    with caplog.at_level("ERROR"):
        results = search.search_top_k(query_embedding)

    # Assert
    assert results == []
    assert "Workflow vector search failed" in caplog.text