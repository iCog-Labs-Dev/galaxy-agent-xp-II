class ToolMetadataRelations:
    def tool_category(self, tool_node, cat_node):
        return ("BELONGS_TO", tool_node, cat_node, {})