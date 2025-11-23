class ToolMetadataBuilder:
    def build_tool(self, tool):
        return {
            "label": "Tool",
            "properties": {
                "name": tool["name"],
                "description": tool.get("description", ""),
                "version": tool.get("version", ""),
                "help": tool.get("help", "")
            }
        }

    def build_category(self, cat):
        return {
            "label": "ToolCategory",
            "properties": {
                "name": cat
            }
        }
