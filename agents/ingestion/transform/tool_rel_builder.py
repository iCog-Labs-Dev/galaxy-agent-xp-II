class ToolMetadataRelations:
    def tool_category(self, tool_node: dict, cat_node: dict):
        return (
            "BELONGS_TO",
            "Tool", tool_node["properties"],
            "ToolCategory", cat_node["properties"],
            {}
        )

    def tool_has_input(self, tool_node: dict, input_node: dict):
        return (
            "TOOL_HAS_INPUT",
            "Tool", tool_node["properties"],
            "ToolInput", input_node["properties"],
            {}
        )

    def tool_has_output(self, tool_node: dict, output_node: dict):
        return (
            "TOOL_HAS_OUTPUT",
            "Tool", tool_node["properties"],
            "ToolOutput", output_node["properties"],
            {}
        )