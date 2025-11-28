import json
from typing import Optional

class ToolLoader:
    def __init__(self, neo):
        self.neo = neo
        # Try multiple import styles so this file can be executed as a module
        # or as a script. Preferred: package-relative. Fallback: sibling package.
        try:
            from ..transform.tool_node_builder import ToolMetadataBuilder
            from ..transform.tool_rel_builder import ToolMetadataRelations
        except Exception:
            # Fallback when running as a script from agents/ingestion
            from transform.tool_node_builder import ToolMetadataBuilder
            from transform.tool_rel_builder import ToolMetadataRelations

        self.build = ToolMetadataBuilder()
        self.rel = ToolMetadataRelations()

    def import_file(self, path: str):
        with open(path, "r", encoding="utf-8") as f:
            tools = json.load(f)

        for t in tools:
            try:
                self.process_tool(t)
            except Exception as e:
                print(f"[tool_loader] error processing tool {t.get('id')}: {e}")

    def process_tool(self, t: dict):
        tool_node = self.build.build_tool(t)
        tool_props = tool_node["properties"]
        tool_id = tool_props.get("tool_id")
        if not tool_id:
            # skip invalid entries
            print(f"[tool_loader] skipping tool without id: {t}")
            return

        # Merge Tool node (unique by tool_id)
        self.neo.merge_node(tool_node["label"], tool_props, unique_key="tool_id")

        # Categories -> ToolCategory nodes and BELONGS_TO rels
        for cat in t.get("categories", []):
            cat_node = self.build.build_category(cat)
            self.neo.merge_node(cat_node["label"], cat_node["properties"], unique_key="category_id")
            rel = self.rel.tool_category(tool_node, cat_node)
            self.neo.merge_rel(*rel)

        # Inputs
        for inp in t.get("inputs", []):
            input_node = self.build.build_input_node(tool_id, inp)
            self.neo.merge_node(input_node["label"], input_node["properties"], unique_key="input_uid")
            rel = self.rel.tool_has_input(tool_node, input_node)
            self.neo.merge_rel(*rel)

        # Outputs
        for out in t.get("outputs", []):
            output_node = self.build.build_output_node(tool_id, out)
            self.neo.merge_node(output_node["label"], output_node["properties"], unique_key="output_uid")
            rel = self.rel.tool_has_output(tool_node, output_node)
            self.neo.merge_rel(*rel)
