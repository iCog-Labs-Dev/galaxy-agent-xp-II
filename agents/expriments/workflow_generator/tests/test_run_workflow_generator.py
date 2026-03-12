import json
import sys
import types
from unittest.mock import mock_open, patch

import pytest


def _install_minimal_third_party_stubs():
    """Install lightweight stubs for heavy third-party modules."""
    for name in ["tensorflow", "h5py"]:
        if name not in sys.modules:
            sys.modules[name] = types.ModuleType(name)

    # Stub out dotenv.load_dotenv
    dotenv = types.ModuleType("dotenv")

    def fake_load_dotenv(*args, **kwargs):
        return None

    dotenv.load_dotenv = fake_load_dotenv
    sys.modules["dotenv"] = dotenv


@pytest.fixture(autouse=True)
def stub_external_modules():
    # Automatically install stubs before each test in this module
    _install_minimal_third_party_stubs()


def test_main_happy_path_with_mocks(monkeypatch):
    # Arrange
    # Stub model manager in its import location path so import succeeds
    model_module = types.ModuleType("agents.expriments.Next_Tool_Recommendation.model")

    class FakeModelManager:
        def __init__(self, path):
            self.path = path
            self.loaded = False

        def load(self):
            self.loaded = True

        def get_model(self):
            class DummyModel:
                def predict(self, x, verbose=0):
                    return None, None

            return DummyModel()

        def get_metadata(self):
            reverse_dict = {"1": "tool_a", "2": "tool_b"}
            forward_dict = {"tool_a": 1, "tool_b": 2}
            class_weights = [1.0, 1.0]
            return reverse_dict, forward_dict, class_weights

    model_module.ModelManager = FakeModelManager
    model_module.build_transformer_model = lambda *args, **kwargs: None
    sys.modules["agents.expriments.Next_Tool_Recommendation.model"] = model_module

    # Import after stubbing
    from agents.expriments.workflow_generator import run_workflow_generator

    # Patch environment configuration
    monkeypatch.setenv("WORKFLOW_GENERATOR_MODEL_PATH", "/fake/model/path.h5")
    monkeypatch.setenv("WORKFLOW_GENERATOR_BRIDGE_DICT_PATH", "/fake/dict/path.json")
    monkeypatch.setenv("GALAXY_URL", "http://galaxy.example.com")
    monkeypatch.setenv("GALAXY_API_KEY", "fake-api-key")

    # Mock bridge dictionary loading
    tool_map = {"tool_a": "full_id_a"}

    def fake_json_load(f):
        return tool_map

    mocked_open = mock_open()
    predicted_chain = ["tool_a", "tool_b"]

    # Capture json.dump for the output file
    dumped = {}

    def fake_json_dump(obj, f, indent=4):
        dumped.update(obj)

    # Mock validator
    class FakeValidator:
        last_instance = None

        def __init__(self, url, api_key):
            self.url = url
            self.api_key = api_key
            self.installed_tools = {
                "tool_a": {"full_id": "validated_full_id_a"},
                "tool_b": {"full_id": "validated_full_id_b"},
            }
            FakeValidator.last_instance = self

        def validate_and_fix_chain(self, chain, tool_mapping):
            return ["tool_a", "tool_b"]

    with patch(
        "agents.expriments.workflow_generator.run_workflow_generator.os.path.exists",
        return_value=True,
    ), patch(
        "agents.expriments.workflow_generator.run_workflow_generator.open", mocked_open
    ), patch(
        "agents.expriments.workflow_generator.run_workflow_generator.json.load",
        side_effect=fake_json_load,
    ), patch(
        "agents.expriments.workflow_generator.run_workflow_generator.generate_tool_sequence",
        return_value=predicted_chain,
    ), patch(
        "agents.expriments.workflow_generator.run_workflow_generator.GalaxyValidator",
        FakeValidator,
    ), patch(
        "agents.expriments.workflow_generator.run_workflow_generator.create_galaxy_workflow"
    ) as create_workflow_mock, patch(
        "agents.expriments.workflow_generator.run_workflow_generator.json.dump",
        side_effect=fake_json_dump,
    ):
        # Configure workflow creation mock
        def fake_create_workflow(final_chain, tool_mapping, workflow_name):
            return {"steps": {}, "name": workflow_name, "chain": final_chain}

        create_workflow_mock.side_effect = fake_create_workflow

        # Act
        run_workflow_generator.main()

        # Assert
        # Ensure validator was constructed with environment-provided URL and key
        assert FakeValidator.last_instance is not None
        assert FakeValidator.last_instance.url == "http://galaxy.example.com"
        assert FakeValidator.last_instance.api_key == "fake-api-key"

        create_workflow_mock.assert_called_once()
        _, kwargs = create_workflow_mock.call_args
        assert kwargs["workflow_name"] == "AI_Validated_Workflow"
        assert kwargs["tool_mapping"]["tool_a"] == "validated_full_id_a"
        assert kwargs["tool_mapping"]["tool_b"] == "validated_full_id_b"

        assert dumped.get("name") == "AI_Validated_Workflow"


def test_main_handles_missing_bridge_dictionary(monkeypatch, capsys):
    # Arrange
    # Ensure stubbed external modules are in place
    _install_minimal_third_party_stubs()

    # Stub model manager again for this test
    model_module = types.ModuleType("agents.expriments.Next_Tool_Recommendation.model")

    class FakeModelManager:
        def __init__(self, path):
            self.path = path

        def load(self):
            pass

        def get_model(self):
            class DummyModel:
                def predict(self, x, verbose=0):
                    return None, None

            return DummyModel()

        def get_metadata(self):
            return {"1": "tool_a"}, {"tool_a": 1}, [1.0]

    model_module.ModelManager = FakeModelManager
    model_module.build_transformer_model = lambda *args, **kwargs: None
    sys.modules["agents.expriments.Next_Tool_Recommendation.model"] = model_module

    from agents.expriments.workflow_generator import run_workflow_generator

    with patch(
        "agents.expriments.workflow_generator.run_workflow_generator.os.path.exists",
        return_value=False,
    ), patch(
        "agents.expriments.workflow_generator.run_workflow_generator.generate_tool_sequence",
        return_value=["tool_a"],
    ), patch(
        "agents.expriments.workflow_generator.run_workflow_generator.GalaxyValidator"
    ) as validator_cls, patch(
        "agents.expriments.workflow_generator.run_workflow_generator.create_galaxy_workflow",
        return_value={"steps": {}, "name": "AI_Validated_Workflow"},
    ), patch(
        "agents.expriments.workflow_generator.run_workflow_generator.open",
        mock_open(),
    ), patch(
        "agents.expriments.workflow_generator.run_workflow_generator.json.dump"
    ):
        class FakeValidator:
            def __init__(self, url, api_key):
                self.installed_tools = {
                    "tool_a": {"full_id": "validated_full_id_a"},
                }

            def validate_and_fix_chain(self, chain, tool_mapping):
                return chain

        validator_cls.side_effect = FakeValidator

        # Act
        run_workflow_generator.main()
    captured = capsys.readouterr()

    # Assert
    # Should log a warning about missing bridge dictionary but still complete
    assert "Bridge dictionary not found" in captured.out

