# agents/tests/test_graph_queries.py
import pytest
from unittest.mock import MagicMock
from agents.graphRAG.retrieval.graph_queries import GraphQueries


# ---------------- FIXTURES ---------------- #
@pytest.fixture
def mock_session():
    """
    Returns a mock Neo4j session object with a fake `run` method.
    """
    session = MagicMock()
    # The session.run() will return an iterable of dict-like records
    session.run.return_value = [
        {"tool_id": "t1", "name": "ToolA", "version": "1.0", "description": "Test tool"}
    ]
    return session


# ---------------- TEST QUERY STRINGS ---------------- #
def test_tool_by_id_query():
    query = GraphQueries.tool_by_id()
    assert "MATCH (t:Tool {tool_id: $tool_id})" in query
    assert "RETURN" in query


def test_tools_by_category_query():
    query = GraphQueries.tools_by_category()
    assert "MATCH (c:ToolCategory {name: $category_name})" in query
    assert "RETURN" in query


def test_workflow_by_id_query():
    query = GraphQueries.workflow_by_id()
    assert "MATCH (w:Workflow {workflow_id: $workflow_id})" in query
    assert "RETURN" in query


def test_search_nodes_by_name_query():
    query = GraphQueries.search_nodes_by_name()
    assert "WHERE toLower(n.name) CONTAINS toLower($name)" in query
    assert "LIMIT $limit" in query


# ---------------- TEST EXECUTION UTILITIES ---------------- #
def test_run_query_returns_records(mock_session):
    result = GraphQueries.run_query(mock_session, "MATCH (n) RETURN n LIMIT 1")
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["tool_id"] == "t1"


def test_run_query_handles_exception():
    session = MagicMock()
    session.run.side_effect = Exception("DB failure")
    result = GraphQueries.run_query(session, "INVALID QUERY")
    assert result == []


def test_fetch_one_returns_single_record(mock_session):
    record = GraphQueries.fetch_one(mock_session, "MATCH (n) RETURN n LIMIT 1")
    assert isinstance(record, dict)
    assert record["tool_id"] == "t1"


def test_fetch_one_returns_none_on_empty_result():
    session = MagicMock()
    session.run.return_value = []
    record = GraphQueries.fetch_one(session, "MATCH (n) RETURN n LIMIT 1")
    assert record is None
