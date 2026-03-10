from unittest.mock import patch

import pytest


def test_galaxy_validator_populates_installed_tools_cache():
    # Arrange: patch the GalaxyInstance used inside validator.py so no real HTTP calls occur
    class FakeToolsClient:
        def get_tools(self):
            return [
                {
                    "id": "toolshed.g2.bx.psu.edu/repos/devteam/bwa/0.7.17.4",
                    "version": "0.7.17.4",
                },
                {
                    "id": "simple_tool",
                    "version": "1.0.0",
                },
            ]

    class FakeGalaxyInstance:
        def __init__(self, url, key):
            self.url = url
            self.key = key
            self.tools = FakeToolsClient()

    with patch(
        "agents.expriments.workflow_generator.validator.GalaxyInstance",
        FakeGalaxyInstance,
    ):
        from agents.expriments.workflow_generator.validator import GalaxyValidator

        # Act
        validator = GalaxyValidator("http://example.com", "fake-key")

    # Assert
    assert "bwa" in validator.installed_tools
    assert "simple_tool" in validator.installed_tools
    bwa_info = validator.installed_tools["bwa"]
    assert bwa_info["full_id"].endswith("/bwa/0.7.17.4")
    assert bwa_info["version"] == "0.7.17.4"


@pytest.mark.parametrize(
    "predicted_chain, installed, expected",
    [
        (["bwa", "samtools_view"], {"bwa", "samtools_view"}, ["bwa", "samtools_view"]),
        (["bwa", "missing_tool"], {"bwa"}, ["bwa"]),
        ([], {"bwa"}, []),
    ],
)
def test_validate_and_fix_chain_filters_missing_tools(
    predicted_chain, installed, expected, capsys
):
    # Arrange
    # Create a lightweight GalaxyValidator instance without calling real Galaxy
    from agents.expriments.workflow_generator.validator import GalaxyValidator

    validator = object.__new__(GalaxyValidator)
    validator.gi = None
    validator.installed_tools = {name: {"full_id": name, "version": "1.0.0"} for name in installed}

    # Act
    result = validator.validate_and_fix_chain(predicted_chain, tool_mapping={})
    captured = capsys.readouterr()

    # Assert
    assert result == expected
    for tool in predicted_chain:
        if tool not in installed:
            assert f"Tool '{tool}' not found" in captured.out

