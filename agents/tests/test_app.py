# agents/tests/test_app.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from agents.app import app

# ---------------- CLIENT FIXTURE ---------------- #
@pytest.fixture
def client():
    return TestClient(app)

# ---------------- MOCK AGENTS ---------------- #
@pytest.fixture
def mock_tool_agent():
    with patch("agents.app.tool_agent", autospec=True) as mock_agent:
        mock_agent.suggest_tools.return_value = [
            {"tool_id": "tool1", "name": "FastQC"}
        ]
        yield mock_agent

@pytest.fixture
def mock_workflow_agent():
    with patch("agents.app.workflow_agent", autospec=True) as mock_agent:
        mock_agent.suggest_workflows.return_value = [
            {
                "workflow_id": "wf1",
                "name": "RNA-Seq Pipeline",
                "category": "RNA Analysis",
                "tools_used": ["FastQC", "STAR"],
                "readme_excerpt": "This pipeline performs RNA-Seq analysis",
                "score": 0.95
            }
        ]
        yield mock_agent

@pytest.fixture
def mock_summary_agent():
    with patch("agents.app.summary_agent", autospec=True) as mock_agent:
        mock_agent.summarize_tools_suggestions.return_value = "Tool summary"
        mock_agent.summarize_workflows_suggestions.return_value = "Workflow summary"
        yield mock_agent

@pytest.fixture
def mock_classify_query():
    with patch("agents.app.classify_query") as mock_fn:
        def side_effect(q):
            if "tool" in q:
                return {"label": "tool"}
            elif "workflow" in q:
                return {"label": "workflow"}
            else:
                return {"label": "both"}
        mock_fn.side_effect = side_effect
        yield mock_fn

@pytest.fixture
def mock_answer_gen():
    with patch("agents.app.answer_gen", autospec=True) as mock_gen:
        mock_gen.generate.return_value = "Generated answer"
        yield mock_gen

# ---------------- BASIC ROUTES ---------------- #
def test_root(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "Welcome" in res.json()["message"]

def test_health_check(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

# ---------------- TOOL ENDPOINTS ---------------- #
def test_suggest_tools(client, mock_tool_agent):
    payload = {"query": "tool for qc", "top_k": 2}
    res = client.post("/suggest-tools", json=payload)
    assert res.status_code == 200
    assert "results" in res.json()
    mock_tool_agent.suggest_tools.assert_called_once_with("tool for qc", 2)

def test_suggest_tools_enhanced(client, mock_tool_agent, mock_summary_agent):
    payload = {"query": "enhanced tool", "top_k": 2}
    res = client.post("/suggest-tools-enhanced", json=payload)
    assert res.status_code == 200
    assert res.json()["summary"] == "Tool summary"
    mock_summary_agent.summarize_tools_suggestions.assert_called_once()

# ---------------- WORKFLOW ENDPOINTS ---------------- #
def test_suggest_workflows(client, mock_workflow_agent):
    payload = {"query": "workflow for rna", "top_k": 2}
    res = client.post("/suggest-workflows", json=payload)
    assert res.status_code == 200
    assert "results" in res.json()
    mock_workflow_agent.suggest_workflows.assert_called_once_with("workflow for rna", 2)

def test_suggest_workflows_enhanced(client, mock_workflow_agent, mock_summary_agent):
    payload = {"query": "enhanced workflow", "top_k": 2}
    res = client.post("/suggest-workflows-enhanced", json=payload)
    assert res.status_code == 200
    assert res.json()["summary"] == "Workflow summary"
    mock_summary_agent.summarize_workflows_suggestions.assert_called_once()

# ---------------- RECOMMENDATION ENDPOINT ---------------- #
def test_recommend_tool(client, mock_classify_query, mock_tool_agent, mock_answer_gen):
    payload = {"query": "tool suggestion", "top_k": 2}
    res = client.post("/recommend", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "tools" in data
    assert "workflows" not in data
    mock_tool_agent.suggest_tools.assert_called_once()
    mock_answer_gen.generate.assert_called_once()

def test_recommend_workflow(client, mock_classify_query, mock_workflow_agent, mock_answer_gen):
    payload = {"query": "workflow suggestion", "top_k": 2}
    res = client.post("/recommend", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "workflows" in data
    assert "tools" not in data
    mock_workflow_agent.suggest_workflows.assert_called_once()
    mock_answer_gen.generate.assert_called_once()

def test_recommend_both(client, mock_classify_query, mock_tool_agent, mock_workflow_agent, mock_answer_gen):
    payload = {"query": "general recommendation", "top_k": 2}
    res = client.post("/recommend", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "tools" in data
    assert "workflows" in data
    mock_tool_agent.suggest_tools.assert_called_once()
    mock_workflow_agent.suggest_workflows.assert_called_once()
    mock_answer_gen.generate.assert_called_once()

# ---------------- ERROR HANDLING ---------------- #
def test_recommend_internal_error(client):
    with patch("agents.app.classify_query", side_effect=Exception("Mocked internal error")):
        payload = {"query": "trigger error", "top_k": 2}
        res = client.post("/recommend", json=payload)
        assert res.status_code == 500
        assert "Mocked internal error" in res.json()["detail"]
