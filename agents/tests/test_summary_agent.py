# agents/tests/test_summary_agent_new.py
import os
import pytest
from unittest.mock import MagicMock, patch
import agents.summary_agent as summary_agent

# ---------------- FIXTURES ---------------- #
@pytest.fixture
def mock_openai_generate():
    """Mock OpenAI .generate() method."""
    return MagicMock(return_value="OpenAI mock output")

@pytest.fixture
def mock_gemini_generate():
    """Mock Gemini .generate() method."""
    return MagicMock(return_value="Gemini mock output")

# ---------------- PROVIDER SELECTION TESTS ---------------- #
@pytest.mark.parametrize(
    "env_openai, env_gemini, provider_arg, expected_cls, expected_output",
    [
        ("k_openai", "k_gemini", "openai", "OpenAIModel", "OpenAI mock output"),
        ("k_openai", "k_gemini", "gemini", "GeminiModel", "Gemini mock output"),
        ("k_openai", "k_gemini", None, "OpenAIModel", "OpenAI mock output"),
        ("k_openai", None, None, "OpenAIModel", "OpenAI mock output"),
        (None, "k_gemini", None, "GeminiModel", "Gemini mock output"),
    ],
)
def test_get_llm_selection(env_openai, env_gemini, provider_arg, expected_cls, expected_output,
                           mock_openai_generate, mock_gemini_generate, monkeypatch):
    # Set environment variables
    with monkeypatch.context() as m:
        if env_openai is None:
            m.delenv("OPENAI_API_KEY", raising=False)
        else:
            m.setenv("OPENAI_API_KEY", env_openai)
        if env_gemini is None:
            m.delenv("GEMINI_API_KEY", raising=False)
        else:
            m.setenv("GEMINI_API_KEY", env_gemini)

        # Patch provider classes
        with patch.object(summary_agent, "OpenAIModel", autospec=True) as MockOpenAI, \
             patch.object(summary_agent, "GeminiModel", autospec=True) as MockGemini:

            MockOpenAI.return_value.generate = mock_openai_generate
            MockGemini.return_value.generate = mock_gemini_generate

            model = summary_agent.get_llm(provider_arg)

            if expected_cls == "OpenAIModel":
                assert isinstance(model, MockOpenAI.return_value.__class__)
                assert model.generate("prompt") == expected_output
            else:
                assert isinstance(model, MockGemini.return_value.__class__)
                assert model.generate("prompt") == expected_output

# Fallback behavior tests
def test_fallback_when_one_missing(mock_openai_generate, mock_gemini_generate, monkeypatch):
    # OpenAI missing → fallback to Gemini
    with monkeypatch.context() as m:
        m.delenv("OPENAI_API_KEY", raising=False)
        m.setenv("GEMINI_API_KEY", "k_gemini")
        with patch.object(summary_agent, "GeminiModel", autospec=True) as MockGemini:
            MockGemini.return_value.generate = mock_gemini_generate
            model = summary_agent.get_llm("openai")
            assert model.generate("x") == "Gemini mock output"

    # Gemini missing → fallback to OpenAI
    with monkeypatch.context() as m:
        m.delenv("GEMINI_API_KEY", raising=False)
        m.setenv("OPENAI_API_KEY", "k_openai")
        with patch.object(summary_agent, "OpenAIModel", autospec=True) as MockOpenAI:
            MockOpenAI.return_value.generate = mock_openai_generate
            model = summary_agent.get_llm("gemini")
            assert model.generate("x") == "OpenAI mock output"

# Invalid provider should raise ValueError
def test_invalid_provider_raises(monkeypatch):
    with monkeypatch.context() as m:
        m.setenv("OPENAI_API_KEY", "k_openai")
        m.setenv("GEMINI_API_KEY", "k_gemini")
        with pytest.raises(ValueError, match="Unknown LLM provider"):
            summary_agent.get_llm("invalid_provider")

# No keys at all → ValueError
def test_no_keys_raises(monkeypatch):
    with monkeypatch.context() as m:
        m.delenv("OPENAI_API_KEY", raising=False)
        m.delenv("GEMINI_API_KEY", raising=False)
        with pytest.raises(ValueError, match="Missing GEMINI_API_KEY and OPENAI_API_KEY"):
            summary_agent.get_llm()

# ---------------- SUMMARIZATION TESTS ---------------- #
def test_summarize_tools(mock_openai_generate):
    tools = [{"name": "ToolA", "category": "Bio", "description": "DescA"}]
    fake_llm = MagicMock(generate=mock_openai_generate)
    agent = summary_agent.SummaryAgent(llm=fake_llm)

    result = agent.summarize_tools_suggestions(tools, "Query")
    assert result == "OpenAI mock output"
    fake_llm.generate.assert_called_once()

def test_summarize_workflows(mock_openai_generate):
    workflows = [{"name": "WF1", "category": "CatX", "score": 0.95, "readme_excerpt": "Details"}]
    fake_llm = MagicMock(generate=mock_openai_generate)
    agent = summary_agent.SummaryAgent(llm=fake_llm)

    result = agent.summarize_workflows_suggestions(workflows, "Query")
    assert result == "OpenAI mock output"
    fake_llm.generate.assert_called_once()
