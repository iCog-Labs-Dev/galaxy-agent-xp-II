class ToolMetadataBuilder:
    """Build node dictionaries for tools, categories, inputs, and outputs.

    Each method returns a dict with keys `label` and `properties` suitable for
    use with `Neo4jClient.merge_node(label, properties, unique_key=...)`.
    """

    def build_tool(self, tool: dict) -> dict:
        # Include embedding if it exists
        return {
            "label": "Tool",
            "properties": {
                "tool_id": tool.get("id"),
                "name": tool.get("name"),
                "description": tool.get("description", ""),
                "version": tool.get("version", ""),
                "help": tool.get("help", ""),
                "embedding": tool.get("embedding")  # embedding added here
            }
        }

    def build_category(self, category_name: str) -> dict:
        # Create a stable category id (slug) for uniqueness
        cid = category_name.strip().lower().replace(" ", "-")
        return {
            "label": "ToolCategory",
            "properties": {
                "category_id": cid,
                "name": category_name
            }
        }

    def build_input_node(self, tool_id: str, inp: dict) -> dict:
        name = inp.get("name") or inp.get("id") or ""
        accepts = inp.get("accepts") or inp.get("formats") or None
        accepts_val = None
        if isinstance(accepts, (list, tuple)):
            accepts_val = ", ".join(map(str, accepts))
        elif accepts is not None:
            accepts_val = str(accepts)

        return {
            "label": "ToolInput",
            "properties": {
                "input_uid": f"{tool_id}::input::{name}",
                "tool_id": tool_id,
                "name": name,
                "type": inp.get("type", ""),
                "accepts": accepts_val or ""
            }
        }

    def build_output_node(self, tool_id: str, out: dict) -> dict:
        name = out.get("name") or out.get("id") or ""
        fmt = out.get("format") or out.get("format_type") or None
        return {
            "label": "ToolOutput",
            "properties": {
                "output_uid": f"{tool_id}::output::{name}",
                "tool_id": tool_id,
                "name": name,
                "format": fmt or ""
            }
        }
