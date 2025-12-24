# agents/tests/test_classification_service.py
import sys
import json
import types
import pytest
from unittest.mock import MagicMock, patch

MODULE_PATH = "agents.classification_service"

# ------------------ Helper Functions ------------------ #
def _make_fake_openai_client(response_json):
    fake_client = MagicMock()
    fake_resp = MagicMock()
    fake_choice = MagicMock()
    fake_message = MagicMock()
    fake_message.content.strip.return_value = json.dumps(response_json)
    fake_choice.message = fake_message
    fake_resp.choices = [fake_choice]
    fake_client.chat.completions.create.return_value = fake_resp
    return fake_client

def _inject_fake_genai_module(response_json):
    genai_mod = types.ModuleType("google.generativeai")
    class FakeModel:
        def generate_content(self, prompt):
            fake_resp = types.SimpleNamespace()
            fake_resp.text = json.dumps(response_json)
            return fake_resp
    genai_mod.GenerativeModel = lambda name: FakeModel()
    genai_mod.configure = lambda api_key: None

    google_mod = types.ModuleType("google")
    google_mod.generativeai = genai_mod

    sys.modules["google"] = google_mod
    sys.modules["google.generativeai"] = genai_mod

def import_fresh_module(openai_key=False, gemini_key=False):
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
def test_classify_query_openai(monkeypatch):
    response_json = {"reasoning": "Workflow query", "label": "workflow", "confidence": 0.9}
    svc = import_fresh_module(openai_key=True)
    monkeypatch.setattr(svc, "_classify_with_openai", lambda prompt: json.dumps(response_json))

    result = svc.classify_query("Analyze RNA-seq")
    assert result["label"] == "workflow"
    assert result["confidence"] == 0.9
    assert result["reasoning"] == "Workflow query"

def test_classify_query_gemini(monkeypatch):
    response_json = {"reasoning": "Tool request", "label": "tool", "confidence": 0.75}
    _inject_fake_genai_module(response_json)
    svc = import_fresh_module(openai_key=False, gemini_key=True)

    result = svc.classify_query("Run FastQC")
    assert result["label"] == "tool"
    assert result["confidence"] == 0.75
    assert result["reasoning"] == "Tool request"

def test_classify_query_invalid_json(monkeypatch):
    svc = import_fresh_module(openai_key=True)
    monkeypatch.setattr(svc, "_classify_with_openai", lambda prompt: "not-a-json")

    result = svc.classify_query("Trigger invalid JSON")
    assert result["label"] == "both"
    assert result["confidence"] == 0.5
    assert result["reasoning"] == "Fallback classification"

def test_classify_query_no_keys(monkeypatch):
    svc = import_fresh_module(openai_key=False, gemini_key=False)
    result = svc.classify_query("No API keys query")
    assert result["label"] == "both"
    assert result["confidence"] == 0.5
    assert result["reasoning"] == "All LLMs exhausted"
