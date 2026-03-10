import json

import pytest


def test_create_galaxy_workflow_with_explicit_mapping():
    # Arrange
    predicted_tools = ["bwa", "join_samples", "bamProcessor"]
    tool_mapping = {
        "bwa": "toolshed.g2.bx.psu.edu/repos/devteam/bwa/0.7.17.4",
        "join_samples": "toolshed.g2.bx.psu.edu/repos/devteam/join/1.0.0",
        "bamProcessor": "toolshed.g2.bx.psu.edu/repos/devteam/bam_processor/1.0.0",
    }

    from agents.expriments.workflow_generator.generate_ga_file import (
        create_galaxy_workflow,
    )

    # Act
    workflow = create_galaxy_workflow(
        predicted_tools, tool_mapping=tool_mapping, workflow_name="Test_Workflow"
    )

    # Assert
    assert workflow["a_galaxy_workflow"] == "true"
    assert workflow["name"] == "Test_Workflow"
    assert "steps" in workflow

    steps = workflow["steps"]
    # Step 0: data_input
    assert steps["0"]["id"] == 0
    assert steps["0"]["type"] == "data_input"

    # Step 1: bwa tool, single input from step 0
    step1 = steps["1"]
    assert step1["tool_id"] == tool_mapping["bwa"]
    assert step1["id"] == 1
    assert step1["input_connections"]["input"]["id"] == 0

    # Step 2: join_samples should create an extra side-input step and use two inputs
    step2 = steps["2"]
    assert step2["tool_id"] == tool_mapping["join_samples"]
    assert step2["id"] == 2
    assert "input1" in step2["input_connections"]
    assert "input2" in step2["input_connections"]

    side_input_step_id = step2["input_connections"]["input2"]["id"]
    assert str(side_input_step_id) in steps
    side_step = steps[str(side_input_step_id)]
    assert side_step["type"] == "data_input"

    # Step 3: bamProcessor should use the 'bam' port when appropriate
    step3 = steps["3"]
    assert step3["tool_id"] == tool_mapping["bamProcessor"]
    assert step3["id"] == 3
    assert "bam" in step3["input_connections"]
    assert step3["input_connections"]["bam"]["id"] == 2

    # Only the last step exposes workflow_outputs
    assert steps["1"]["workflow_outputs"] == []
    assert steps["2"]["workflow_outputs"] == []
    assert steps["3"]["workflow_outputs"] != []


def test_create_galaxy_workflow_marks_missing_tool_with_warning():
    # Arrange
    predicted_tools = ["unknown_tool"]
    tool_mapping = {}

    from agents.expriments.workflow_generator.generate_ga_file import (
        create_galaxy_workflow,
    )

    # Act
    workflow = create_galaxy_workflow(predicted_tools, tool_mapping=tool_mapping)

    # Assert
    step1 = workflow["steps"]["1"]
    assert step1["tool_id"] == "unknown_tool"
    assert "⚠️ Note:" in step1["annotation"]

