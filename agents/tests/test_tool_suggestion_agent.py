import json
from unittest.mock import MagicMock

import numpy as np
import pytest

from agents.suggesting_agent import ToolSuggestionAgent


def _fake_pytorch_cos_sim(query_embedding: np.ndarray, embeddings: np.ndarray) -> np.ndarray:
    """
    Minimal cosine-similarity implementation returning shape (1, n_tools),
    matching the subset of the sentence_transformers util API that the agent uses.
    """
    query_embedding = np.asarray(query_embedding, dtype=np.float32)
    embeddings = np.asarray(embeddings, dtype=np.float32)

    if query_embedding.ndim == 1:
        query_embedding = query_embedding[None, :]

    query_norm = query_embedding / (np.linalg.norm(query_embedding, axis=1, keepdims=True) + 1e-12)
    emb_norm = embeddings / (np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-12)
    return query_norm @ emb_norm.T


@pytest.fixture()
def agent_from_test_data(monkeypatch) -> ToolSuggestionAgent:
    """
    Build a ToolSuggestionAgent instance without calling __init__ (avoids loading
    transformer models/large embedding files) and instead uses deterministic fake
    embeddings derived from the JSON test data.
    """
    test_file = "agents/tests/data/test_data.json"
    with open(test_file, "r", encoding="utf-8") as f:
        cases = json.load(f)

    tool_names = []
    prompt_to_tool = {}
    for case in cases:
        tool = case["expected_tool"]
        prompt = case["prompt"]
        if tool not in tool_names:
            tool_names.append(tool)
        prompt_to_tool[prompt] = tool

    # Identity embeddings: each tool is perfectly similar to its own one-hot vector.
    embeddings = np.eye(len(tool_names), dtype=np.float32)
    metadata = [{"id": f"tool-{i}", "name": name, "categories": ["Test"]} for i, name in enumerate(tool_names)]

    agent = ToolSuggestionAgent.__new__(ToolSuggestionAgent)
    agent.embeddings = embeddings
    agent.metadata = metadata

    model = MagicMock()

    def fake_encode(query: str, convert_to_numpy=True):
        tool = prompt_to_tool.get(query)
        if tool is None:
            return np.zeros((len(tool_names),), dtype=np.float32)
        idx = tool_names.index(tool)
        return embeddings[idx].copy()

    model.encode.side_effect = fake_encode
    agent.model = model

    # Patch the similarity function used by ToolSuggestionAgent.suggest_tools.
    monkeypatch.setattr(
        "agents.suggesting_agent.util.pytorch_cos_sim",
        _fake_pytorch_cos_sim,
        raising=False,
    )

    return agent


def _load_cases():
    with open("agents/tests/data/test_data.json", "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.parametrize("case", _load_cases())
def test_tool_suggestion_top1_matches_expected(agent_from_test_data: ToolSuggestionAgent, case: dict):
    suggestions = agent_from_test_data.suggest_tools(case["prompt"], top_k=1)
    assert suggestions, "Expected at least one suggestion"
    assert suggestions[0]["name"] == case["expected_tool"]


def test_tool_suggestion_unknown_query_does_not_crash(agent_from_test_data: ToolSuggestionAgent):
    suggestions = agent_from_test_data.suggest_tools("some completely unknown query", top_k=3)
    assert isinstance(suggestions, list)
