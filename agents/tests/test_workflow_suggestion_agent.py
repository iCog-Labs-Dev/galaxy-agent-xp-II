# agents/tests/test_workflow_suggestion_agent.py

import numpy as np
import pytest
from unittest.mock import MagicMock, patch
from agents.workflow_suggestion_agent import WorkflowSuggestionAgent


@pytest.fixture
def fake_metadata():
    return [
        {
            "category": "Bioinformatics",
            "raw_download_url": "https://example.com/workflow1",
            "readme_cleaned": "Processes genomic data using advanced pipelines.",
            "tool_names": ["ToolA", "ToolB"],
            "workflow_repository": "repo1",
        },
        {
            "category": "Chemistry",
            "raw_download_url": "https://example.com/workflow2",
            "readme_cleaned": "Analyzes compounds.",
            "tool_names": ["ToolC"],
            "workflow_repository": "repo2",
        },
    ]


@pytest.fixture
def mock_model():
    mock = MagicMock()
    mock.encode.return_value = np.array([[1.0, 2.0, 3.0]], dtype=np.float32)
    return mock


def test_initialization():
    """Ensure the agent initializes without loading actual files."""
    with patch.object(WorkflowSuggestionAgent, "__init__", lambda self, **kw: None):
        agent = WorkflowSuggestionAgent()
        assert isinstance(agent, WorkflowSuggestionAgent)


def test_suggest_workflows_basic(mock_model, fake_metadata):
    """Test core workflow suggestion logic."""
    with patch.object(WorkflowSuggestionAgent, "__init__", lambda self, **kw: None):
        agent = WorkflowSuggestionAgent()
        agent.model = mock_model
        agent.embeddings = np.array(
            [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]], dtype=np.float32
        )
        agent.metadata = fake_metadata

        # Patch the REAL location of pytorch_cos_sim
        with patch("agents.workflow_suggestion_agent.util.pytorch_cos_sim", return_value=np.array([[0.8, 0.3]])):
            results = agent.suggest_workflows("analyze genome", top_k=1)
            assert len(results) == 1
            assert results[0]["category"] == "Bioinformatics"
            assert results[0]["name"] == "repo1"
            assert np.isclose(results[0]["score"], 0.8)


def test_score_threshold_merging(fake_metadata):
    """Ensure similar-scoring duplicate workflows are merged by name."""
    with patch.object(WorkflowSuggestionAgent, "__init__", lambda self, **kw: None):
        agent = WorkflowSuggestionAgent()
        agent.model = MagicMock()
        agent.model.encode.return_value = np.array([1.0, 2.0, 3.0], dtype=np.float32)
        agent.embeddings = np.array(
            [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]], dtype=np.float32
        )
        agent.metadata = [
            {"workflow_repository": "same_workflow", "category": "Physics"},
            {"workflow_repository": "same_workflow", "category": "Physics"},
        ]

        with patch("agents.workflow_suggestion_agent.util.pytorch_cos_sim", return_value=np.array([[0.2, 0.19]])):
            results = agent.suggest_workflows("physics experiment", top_k=2)
            assert len(results) == 1
            assert results[0]["name"] == "same_workflow"
            assert np.isclose(results[0]["score"], 0.2)


def test_no_results_below_threshold(fake_metadata):
    """Check when all cosine similarities are too low."""
    with patch.object(WorkflowSuggestionAgent, "__init__", lambda self, **kw: None):
        agent = WorkflowSuggestionAgent()
        agent.model = MagicMock()
        agent.model.encode.return_value = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        agent.embeddings = np.array(
            [[1.0, 1.0, 1.0], [2.0, 2.0, 2.0]], dtype=np.float32
        )
        agent.metadata = fake_metadata

        with patch("agents.workflow_suggestion_agent.util.pytorch_cos_sim", return_value=np.array([[0.0, 0.0]])):
            results = agent.suggest_workflows("nothing relevant", top_k=2, score_threshold=0.1)
            assert results == []