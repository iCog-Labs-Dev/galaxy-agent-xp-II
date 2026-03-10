import json
from unittest.mock import mock_open, patch

import pandas as pd
import pytest


@pytest.fixture
def sample_dataframe():
    data = {
        "in_tool": [
            "toolshed.g2.bx.psu.edu/repos/devteam/bwa/0.7.17.4",
            "simple_tool",
        ],
        "out_tool": [
            "toolshed.g2.bx.psu.edu/repos/devteam/samtools_view/1.9.1",
            "another_tool",
        ],
    }
    df = pd.DataFrame(data)
    # Deliberately add extra whitespace to column names to verify stripping
    df.columns = [" in_tool ", " out_tool "]
    return df


def test_build_creates_expected_mapping_and_writes_file(sample_dataframe):
    # Arrange
    read_csv_calls = {}

    def fake_read_csv(path, *args, **kwargs):
        read_csv_calls["args"] = (path,)
        read_csv_calls["kwargs"] = kwargs
        return sample_dataframe
    dumped_payload = {}

    def fake_json_dump(obj, f, indent=4):
        dumped_payload.update(obj)

    with patch(
        "agents.expriments.workflow_generator.create_tool_dict.pd.read_csv",
        side_effect=fake_read_csv,
    ), patch(
        "agents.expriments.workflow_generator.create_tool_dict.json.dump",
        side_effect=fake_json_dump,
    ), patch(
        "agents.expriments.workflow_generator.create_tool_dict.open", mock_open()
    ) as mocked_open:
        from agents.expriments.workflow_generator import create_tool_dict

        # Act
        create_tool_dict.build()

    # Assert
    assert "args" in read_csv_calls
    # Ensure CSV path is correct and separator is as expected
    args = read_csv_calls["args"]
    kwargs = read_csv_calls["kwargs"]
    assert "agents/data/workflow-connections.csv" in args[0]
    assert kwargs.get("sep") == "|"

    # The mapping should use the second-to-last segment for toolshed tools
    assert (
        dumped_payload["bwa"]
        == "toolshed.g2.bx.psu.edu/repos/devteam/bwa/0.7.17.4"
    )
    assert (
        dumped_payload["samtools_view"]
        == "toolshed.g2.bx.psu.edu/repos/devteam/samtools_view/1.9.1"
    )
    # Non-toolshed IDs should be stored as-is
    assert dumped_payload["simple_tool"] == "simple_tool"
    assert dumped_payload["another_tool"] == "another_tool"

    # Verify that the output file is opened for writing
    mocked_open.assert_called_once()
    open_args, open_kwargs = mocked_open.call_args
    assert "agents/data/tool_id_dict.txt" in open_args[0]
    assert open_args[1] == "w"


@pytest.mark.parametrize(
    "full_id, expected_short",
    [
        ("toolshed.g2.bx.psu.edu/repos/devteam/bwa/0.7.17.4", "bwa"),
        ("single_segment_id", "single_segment_id"),
        ("trailing/slash/", "slash"),
    ],
)
def test_build_short_name_extraction_logic(full_id, expected_short):
    # Arrange
    df = pd.DataFrame({"in_tool": [full_id], "out_tool": [None]})
    read_csv_called = {"count": 0}

    def fake_read_csv(*args, **kwargs):
        read_csv_called["count"] += 1
        return df

    captured = {}

    def capture_dump(obj, f, indent=4):
        captured.update(obj)

    with patch(
        "agents.expriments.workflow_generator.create_tool_dict.pd.read_csv",
        side_effect=fake_read_csv,
    ), patch(
        "agents.expriments.workflow_generator.create_tool_dict.json.dump",
        side_effect=capture_dump,
    ), patch(
        "agents.expriments.workflow_generator.create_tool_dict.open", mock_open()
    ):
        from agents.expriments.workflow_generator import create_tool_dict

        # Act
        create_tool_dict.build()

    # Assert
    assert read_csv_called["count"] == 1
    # There should be exactly one entry in the mapping
    assert list(captured.keys()) == [expected_short]
    assert captured[expected_short] == full_id.strip()

