import pytest
from unittest.mock import patch, MagicMock
import agents.summary_agent as summary_agent

# ---------------- FIXTURES ---------------- #
@pytest.fixture
def mock_openai_generate():
    return MagicMock(return_value="OpenAI mock output")

@pytest.fixture
def mock_gemini_generate():
    return MagicMock(return_value="Gemini mock output")

@pytest.fixture
def mock_llm_init():
    with patch.object(summary_agent.OpenAIModel, "__init__", return_value=None) as mock_openai_init, \
         patch.object(summary_agent.GeminiModel, "__init__", return_value=None) as mock_gemini_init:
        yield mock_openai_init, mock_gemini_init


# ---------------- CORE LOGIC TEST ---------------- #
@pytest.mark.parametrize(
    "provider_name, expected_class, mock_output",
    [
        ("openai", summary_agent.OpenAIModel, "OpenAI mock output"),
        ("gemini", summary_agent.GeminiModel, "Gemini mock output"),
        (None, summary_agent.OpenAIModel, "OpenAI mock output"),  # default preference
    ]
)
def test_get_llm_logic(provider_name, expected_class, mock_output,
                       mock_openai_generate, mock_gemini_generate, mock_llm_init):
    """Test LLM selection logic with all external dependencies mocked."""

    with patch("agents.summary_agent.OPENAI_API_KEY", "fake_openai_key"), \
         patch("agents.summary_agent.GEMINI_API_KEY", "fake_gemini_key"), \
         patch("agents.summary_agent.DEFAULT_PROVIDER", "openai"), \
         patch.object(summary_agent, "OpenAIModel", autospec=True) as MockOpenAI, \
         patch.object(summary_agent, "GeminiModel", autospec=True) as MockGemini:

        # Mock generate outputs
        MockOpenAI.return_value.generate = mock_openai_generate
        MockGemini.return_value.generate = mock_gemini_generate

        model = summary_agent.get_llm(provider=provider_name)

        # Validate model type
        if provider_name in ("openai", None):
            assert isinstance(model, MockOpenAI.return_value.__class__)
            assert model.generate("test") == "OpenAI mock output"
        else:
            assert isinstance(model, MockGemini.return_value.__class__)
            assert model.generate("test") == "Gemini mock output"


# ---------------- FALLBACK LOGIC ---------------- #
def test_fallback_to_gemini(mock_openai_generate, mock_gemini_generate):
    """If OpenAI key missing, should fallback to Gemini."""
    with patch("agents.summary_agent.OPENAI_API_KEY", None), \
         patch("agents.summary_agent.GEMINI_API_KEY", "fake_gemini_key"), \
         patch.object(summary_agent, "GeminiModel", autospec=True) as MockGemini:
        MockGemini.return_value.generate = mock_gemini_generate
        model = summary_agent.get_llm("openai")
        assert model.generate("prompt") == "Gemini mock output"


def test_fallback_to_openai(mock_openai_generate, mock_gemini_generate):
    """If Gemini key missing, should fallback to OpenAI."""
    with patch("agents.summary_agent.GEMINI_API_KEY", None), \
         patch("agents.summary_agent.OPENAI_API_KEY", "fake_openai_key"), \
         patch.object(summary_agent, "OpenAIModel", autospec=True) as MockOpenAI:
        MockOpenAI.return_value.generate = mock_openai_generate
        model = summary_agent.get_llm("gemini")
        assert model.generate("prompt") == "OpenAI mock output"


# ---------------- INVALID PROVIDER ---------------- #
def test_invalid_provider_raises():
    """Should raise ValueError for invalid provider."""
    with patch("agents.summary_agent.OPENAI_API_KEY", "fake"), \
         patch("agents.summary_agent.GEMINI_API_KEY", "fake"):
        with pytest.raises(ValueError):
            summary_agent.get_llm("invalid_provider")


# ---------------- SUMMARIZATION TESTS ---------------- #
def test_summarize_tool_suggestions(mock_openai_generate):
    """Ensure summarize_tool_suggestions uses llm.generate correctly."""
    tools = [{"name": "ToolA", "category": "Bio", "description": "DescA"}]
    with patch.object(summary_agent, "llm", MagicMock(generate=mock_openai_generate)):
        result = summary_agent.summarize_tool_suggestions(tools, "Query")
        assert result == "OpenAI mock output"


def test_summarize_workflow_suggestions(mock_openai_generate):
    """Ensure summarize_workflow_suggestions uses llm.generate correctly."""
    workflows = [{"name": "WF1", "category": "CatX", "score": 0.95, "readme_excerpt": "Details"}]
    with patch.object(summary_agent, "llm", MagicMock(generate=mock_openai_generate)):
        result = summary_agent.summarize_workflow_suggestions(workflows, "Query")
        assert result == "OpenAI mock output"
