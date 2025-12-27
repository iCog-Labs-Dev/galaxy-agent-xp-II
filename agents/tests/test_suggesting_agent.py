import pytest
from unittest.mock import patch, MagicMock
import numpy as np
from agents.tool_suggesting_agent import ToolSuggestionAgent

# -------------------- FIXTURES -------------------- #

@pytest.fixture
def mock_model():
    with patch("agents.suggesting_agent.SentenceTransformer") as mock_class:
        mock_instance = mock_class.return_value
        mock_instance.encode.return_value = np.array([1.0, 2.0, 3.0], dtype=np.float32)
        yield mock_instance

@pytest.fixture
def mock_embeddings():
    with patch("agents.suggesting_agent.np.load", return_value=np.array([[1.0, 2.0, 3.0],
                                                                         [4.0, 5.0, 6.0]], dtype=np.float32)) as mock_load:
        yield mock_load

@pytest.fixture
def mock_metadata(tmp_path):
    metadata = [
        {"id": "t1", "name": "ToolOne", "categories": ["CatA"]},
        {"id": "t2", "name": "ToolTwo", "categories": ["CatB"]}
    ]
    file_path = tmp_path / "metadata.json"
    import json
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f)
    yield str(file_path)

# -------------------- TESTS -------------------- #

def test_validate_tool_info_missing_fields():
    agent = ToolSuggestionAgent.__new__(ToolSuggestionAgent)
    tool_info = {"name": "TestTool"}
    validated = agent.validate_tool_info(tool_info)
    assert validated["name"] == "TestTool"
    assert validated["id"] == ""
    assert validated["categories"] == []
    assert validated["category"] == "Uncategorized"

def test_suggest_tools(mock_model, mock_embeddings, mock_metadata):
    with patch.object(ToolSuggestionAgent, "__init__", lambda self, **kwargs: None):
        agent = ToolSuggestionAgent()
        agent.model = mock_model
        agent.embeddings = np.array([[1.0, 2.0, 3.0],
                                     [4.0, 5.0, 6.0]], dtype=np.float32)
        agent.metadata = [
            {"id": "t1", "name": "ToolOne", "categories": ["CatA"]},
            {"id": "t2", "name": "ToolTwo", "categories": ["CatB"]}
        ]
        with patch("agents.suggesting_agent.util.pytorch_cos_sim", return_value=np.array([[0.9, 0.1]]), create=True):
            results = agent.suggest_tools("dummy query", top_k=2)
        assert isinstance(results, list)
        assert len(results) <= 2
        for tool in results:
            assert "id" in tool
            assert "name" in tool
            assert "category" in tool
            assert "score" in tool

def test_score_threshold_logic():
    with patch.object(ToolSuggestionAgent, "__init__", lambda self, **kwargs: None):
        agent = ToolSuggestionAgent()
        agent.model = MagicMock()
        agent.model.encode.return_value = np.array([1.0, 2.0, 3.0], dtype=np.float32)
        agent.embeddings = np.array([[1.0, 2.0, 3.0],
                                     [4.0, 5.0, 6.0]], dtype=np.float32)
        agent.metadata = [
            {"id": "t1", "name": "ToolOne", "categories": ["CatA"]},
            {"id": "t2", "name": "ToolOne", "categories": ["CatA"]}
        ]
        with patch("agents.suggesting_agent.util.pytorch_cos_sim", return_value=np.array([[0.2, 0.15]]), create=True):
            results = agent.suggest_tools("query", top_k=2, score_threshold=0.1)
        names = [t["name"] for t in results]
        assert names.count("ToolOne") == 1
