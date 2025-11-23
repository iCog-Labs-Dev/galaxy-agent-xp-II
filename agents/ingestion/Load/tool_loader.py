import json

class ToolLoader:
    def __init__(self, neo, builder, rel_builder):
        self.neo = neo
        self.build = builder
        self.rel = rel_builder

    def import_file(self, path):
        with open(path) as f:
            tools = json.load(f)

        for t in tools:
            self.process_tool(t)

    def process_tool(self, t):
        tool_node = self.build.build_tool(t)
        self.neo.merge_node(tool_node["label"], tool_node["properties"])

        for cat in t.get("categories", []):
            cat_node = self.build.build_category(cat)
            self.neo.merge_node(cat_node["label"], cat_node["properties"])

            self.neo.merge_rel(
                "BELONGS_TO",
                "Tool", tool_node["properties"],
                "ToolCategory", cat_node["properties"],
                {}
            )
