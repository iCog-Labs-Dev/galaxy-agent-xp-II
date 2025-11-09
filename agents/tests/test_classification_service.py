import sys
import json
import types
import pytest
from unittest.mock import MagicMock, patch

MODULE_PATH = "agents.classification_service"


def _make_fake_openai_client_with_json(response_json):
    """Fake OpenAI client whose chat.completions.create() returns JSON."""
    fake_client = MagicMock()
    fake_resp = MagicMock()
    fake_choice = MagicMock()
    fake_message = MagicMock()
    fake_message.content.strip.return_value = json.dumps(response_json)
    fake_choice.message = fake_message
    fake_resp.choices = [fake_choice]
    fake_client.chat.completions.create.return_value = fake_resp
    return fake_client


def _make_fake_openai_client_with_invalid_json():
    """Fake OpenAI client that returns invalid JSON to trigger parse fallback."""
    fake_client = MagicMock()
    fake_resp = MagicMock()
    fake_choice = MagicMock()
    fake_message = MagicMock()
    fake_message.content.strip.return_value = "not-a-json"
    fake_choice.message = fake_message
    fake_resp.choices = [fake_choice]
    fake_client.chat.completions.create.return_value = fake_resp
    return fake_client


def _inject_fake_genai_module(response_json):
    """Inject fake google.generativeai module that returns predictable JSON."""
    google_pkg = sys.modules.get("google") or types.ModuleType("google")
    genai_mod = types.ModuleType("google.generativeai")

    fake_model = MagicMock()
    fake_resp = MagicMock()
    fake_resp.text.strip.return_value = json.dumps(response_json)
    fake_model.generate_content.return_value = fake_resp

    def GenerativeModel(name):
        return fake_model

    genai_mod.configure = MagicMock()
    genai_mod.GenerativeModel = GenerativeModel

    sys.modules["google"] = google_pkg
    sys.modules["google.generativeai"] = genai_mod


def import_fresh_module(openai_key=False, gemini_key=False):
    """Re-import the classification module with specific env vars."""
    sys.modules.pop(MODULE_PATH, None)

    def fake_getenv(key, default=None):
        if key == "OPENAI_API_KEY":
            return "fake-key" if openai_key else None
        if key == "GEMINI_API_KEY":
            return "fake-key" if gemini_key else None
        return default

    with patch("os.getenv", side_effect=fake_getenv):
        module = __import__(MODULE_PATH, fromlist=["*"])
    return module


# ---------------------- Tests ---------------------- #

def test_classify_query_openai_uses_openai_and_parses(monkeypatch):
    """When OPENAI_API_KEY exists, classification_service should use OpenAI client."""
    openai_json = {"reasoning": "This looks like a workflow.", "label": "workflow", "confidence": 0.87}
    svc = import_fresh_module(openai_key=True)

    fake_client = _make_fake_openai_client_with_json(openai_json)
    monkeypatch.setattr(svc, "_init_openai_client", lambda: fake_client)

    label = svc.classify_query("Find pipeline for RNA-seq")
    assert label == "workflow"


def test_classify_query_gemini_uses_gemini_and_parses(monkeypatch):
    """When OpenAI missing but GEMINI present, Gemini should handle it."""
    gemini_json = {"reasoning": "Single-tool request", "label": "tool", "confidence": 0.74}
    svc = import_fresh_module(openai_key=False, gemini_key=True)
    _inject_fake_genai_module(gemini_json)

    label = svc.classify_query("How to align reads with Bowtie?")
    assert label == "tool"


def test_classify_query_invalid_json_falls_back_to_both(monkeypatch):
    """Invalid JSON from model should cause fallback to 'both'."""
    svc = import_fresh_module(openai_key=True)
    fake_client = _make_fake_openai_client_with_invalid_json()
    monkeypatch.setattr(svc, "_init_openai_client", lambda: fake_client)

    result = svc.classify_query("Give me something that causes parse error")
    assert result == "both"


def test_import_does_not_raise_without_keys():
    """Import should not raise when no API keys exist (safe fallback)."""
    sys.modules.pop(MODULE_PATH, None)
    with patch("os.getenv", return_value=None):
        module = __import__(MODULE_PATH, fromlist=["*"])
        assert hasattr(module, "classify_query")
        result = module.classify_query("Test query with no keys")
        assert result == "both"
