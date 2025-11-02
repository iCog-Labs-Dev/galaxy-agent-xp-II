import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from agents.app import app

client = TestClient(app)

# -------------------- MOCKS -------------------- #

@pytest.fixture
def mock_tool_agent():
    with patch("agents.app.agent", autospec=True) as mock_agent:
        mock_agent.suggest_tools.return_value = [{"tool_id": "tool1", "name": "FastQC"}]
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
def mock_classify():
    with patch("agents.app.classify_query") as mock_fn:
        mock_fn.side_effect = lambda q: "tool" if "tool" in q else "workflow" if "workflow" in q else "both"
        yield mock_fn

@pytest.fixture
def mock_summarize_tool():
    with patch("agents.app.summarize_tool_suggestions") as mock_fn:
        mock_fn.return_value = [{"summary": "Enhanced Tool"}]
        yield mock_fn

@pytest.fixture
def mock_summarize_workflow():
    with patch("agents.app.summarize_workflow_suggestions") as mock_fn:
        mock_fn.return_value = [{"summary": "Enhanced Workflow"}]
        yield mock_fn

# -------------------- BASIC ENDPOINT TESTS -------------------- #

def test_root():
    res = client.get("/")
    assert res.status_code == 200
    assert res.json()["message"].startswith("Welcome")
    assert isinstance(res.json(), dict)

def test_health_check():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
    assert isinstance(res.json(), dict)

# -------------------- TOOL SUGGESTION TESTS -------------------- #

def test_suggest_tools(mock_tool_agent):
    payload = {"query": "tool for qc", "top_k": 2}
    res = client.post("/suggest", json=payload)
    assert res.status_code == 200
    assert "results" in res.json()
    assert isinstance(res.json(), dict)
    mock_tool_agent.suggest_tools.assert_called_once()

def test_suggest_tools_enhanced(mock_tool_agent, mock_summarize_tool):
    payload = {"query": "enhanced tool", "top_k": 2}
    res = client.post("/suggest-tools-enhanced", json=payload)
    assert res.status_code == 200
    assert "results" in res.json()
    assert isinstance(res.json(), dict)
    mock_summarize_tool.assert_called_once()

# -------------------- WORKFLOW SUGGESTION TESTS -------------------- #

def test_suggest_workflows(mock_workflow_agent):
    payload = {"query": "workflow for rna", "top_k": 2}
    res = client.post("/suggest-workflows", json=payload)
    assert res.status_code == 200
    assert "results" in res.json()
    assert isinstance(res.json(), dict)
    mock_workflow_agent.suggest_workflows.assert_called_once()

def test_suggest_workflows_enhanced(mock_workflow_agent, mock_summarize_workflow):
    payload = {"query": "enhanced workflow", "top_k": 2}
    res = client.post("/suggest-workflows-enhanced", json=payload)
    assert res.status_code == 200
    assert "results" in res.json()
    assert isinstance(res.json(), dict)
    mock_summarize_workflow.assert_called_once()

# -------------------- UNIFIED RECOMMENDATION TESTS -------------------- #

def test_recommend_tool_classification(mock_classify, mock_tool_agent):
    payload = {"query": "tool suggestion", "top_k": 2}
    res = client.post("/recommend", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["type"] == "tool"
    assert "results" in data
    assert isinstance(data, dict)

def test_recommend_workflow_classification(mock_classify, mock_workflow_agent):
    payload = {"query": "workflow suggestion", "top_k": 2}
    res = client.post("/recommend", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["type"] == "workflow"
    assert "results" in data
    assert isinstance(data, dict)

def test_recommend_both_classification(mock_classify, mock_tool_agent, mock_workflow_agent):
    payload = {"query": "general recommendation", "top_k": 2}
    res = client.post("/recommend", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["type"] == "both"
    assert "tool_results" in data
    assert "workflow_results" in data
    assert isinstance(data, dict)

# -------------------- ERROR SCENARIOS -------------------- #

def test_recommend_internal_error():
    with patch("agents.app.classify_query", side_effect=Exception("Mocked internal error")):
        payload = {"query": "trigger error", "top_k": 2}
        res = client.post("/recommend", json=payload)
        assert res.status_code == 500
        assert "Mocked internal error" in res.json()["detail"]
        assert isinstance(res.json(), dict)
