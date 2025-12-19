import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from agents.graphRAG.app import app

@pytest.fixture
def client():
    return TestClient(app)

def test_query_graphrag_mock(client):
    with patch("agents.graphRAG.app.rag.run", return_value={
        "cypher": "MATCH (t:Tool) RETURN count(t)",
        "records": [{"count": 14925}],
        "answer": "There are 14925 tools."  
    }):
        payload = {"query": "How many tools exist?"}
        res = client.post("/query-graphrag", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "cypher" in data
        assert "answer" in data
        assert "14925" in str(data["answer"])
