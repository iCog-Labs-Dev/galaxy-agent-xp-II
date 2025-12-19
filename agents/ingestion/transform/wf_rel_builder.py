class RelationshipBuilder:
    def workflow_category(self, workflow, category):
        return (
            "BELONGS_TO",   # update type
            "Workflow", workflow["properties"],
            "Category", category["properties"],
            {}
        )

    def workflow_step(self, workflow, step):
        return (
            "HAS_STEP",
            "Workflow", workflow["properties"],
            "Step", step["properties"],
            {"step_id": step["properties"].get("step_id")}
        )

    def workflow_input(self, workflow, input_node):
        return (
            "HAS_INPUT",
            "Workflow", workflow["properties"],
            "Input", input_node["properties"],
            {}
        )

    def workflow_output(self, workflow, output_node):
        return (
            "HAS_OUTPUT",
            "Workflow", workflow["properties"],
            "Output", output_node["properties"],
            {}
        )

    def step_input(self, step, input_node):
        return (
            "STEP_REQUIRES",
            "Step", step["properties"],
            "Input", input_node["properties"],
            {}
        )

    def step_output(self, step, output_node):
        return (
            "STEP_GENERATES",
            "Step", step["properties"],
            "Output", output_node["properties"],
            {}
        )

    def step_tool(self, step, tool):
        return (
            "USES_TOOL",
            "Step", step["properties"],
            "Tool", tool["properties"],
            {}
        )
