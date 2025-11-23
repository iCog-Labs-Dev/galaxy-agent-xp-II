class RelationshipBuilder:
    def workflow_category(self, workflow, category):
        return ("HAS_WORKFLOW", category, workflow, {})

    def workflow_tool(self, workflow, tool, step):
        return ("USES_TOOL", workflow, tool, {"step": step})

    def workflow_input(self, workflow, input_node):
        return ("REQUIRES", workflow, input_node, {})

    def workflow_output(self, workflow, output_node):
        return ("GENERATES", workflow, output_node, {})
