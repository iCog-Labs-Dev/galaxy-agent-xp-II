class NodeBuilder:
    def create_workflow(self, data):
        return {
            "label": "Workflow",
            "properties": {
                "name": data["workflow_repository"],
                "category": data["category"],
                "readme": data["readme_cleaned"]
            }
        }

    def create_tool(self, name):
        return {
            "label": "Tool",
            "properties": {"name": name}
        }

    def create_category(self, name):
        return {
            "label": "Category",
            "properties": {"name": name}
        }

    def create_io_node(self, label, desc):
        return {
            "label": label,
            "properties": {"description": desc}
        }
