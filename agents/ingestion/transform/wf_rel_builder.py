import hashlib
import json

class RelationshipBuilder:

    # -----------------------
    # Relationships
    # -----------------------
    def workflow_category(self, workflow_node: dict, category_node: dict):
        return (
            "Workflow_BELONGS_TO",
            "Workflow", workflow_node["properties"],
            "WorkflowCategory", category_node["properties"],
            {}
        )

    def workflow_step(self, workflow_node: dict, step_node: dict):
        return (
            "WORKFLOW_HAS_STEP",
            "Workflow", workflow_node["properties"],
            "Step", step_node["properties"],
            {}
        )

    def step_input(self, step_node: dict, input_node: dict):
        return (
            "STEP_INPUT",
            "Step", step_node["properties"],
            "StepInput", input_node["properties"],
            {}
        )
    def step_output(self, step_node: dict, output_node: dict):
        return (
            "STEP_OUTPUT",
            "Step", step_node["properties"],
            "StepOutput", output_node["properties"],
            {}
        )

    def workflow_input(self, workflow_node: dict, input_node: dict):
        return (
            "HAS_INPUT",
            "Workflow", workflow_node["properties"],
            "WorkflowInput", input_node["properties"],
            {}
        )

    def workflow_output(self, workflow_node: dict, output_node: dict):
        return (
            "HAS_OUTPUT",
            "Workflow", workflow_node["properties"],
            "WorkflowOutput", output_node["properties"],
            {}
        )

    def step_tool(self, step_node: dict, tool_node: dict):
        return (
            "USES_TOOL",
            "Step", step_node["properties"],
            "Tool", tool_node["properties"],
            {}
        )
    def workflow_input_semantic(self, workflow_node, input_node):
        return (
            "Workflow_HAS_INPUT",
            "Workflow", workflow_node["properties"],
            "WorkflowInput", input_node["properties"],
            {}
        )
    def workflow_output_semantic(self, workflow_node, output_node):
        return (
            "Workflow_HAS_OUTPUT",
            "Workflow", workflow_node["properties"],
            "WorkflowOutput", output_node["properties"],
            {}
        )
    

    