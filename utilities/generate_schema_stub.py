# generate_schema.py
import yaml
from pathlib import Path
from textwrap import indent

NODES_YAML = Path("agents/ingestion/config/schema.node.yml")
EDGE_YAML   = Path("agents/ingestion/config/schema.edge.yml")

OUT_NODES = Path("agents/ingestion/config/schema_nodes.py")
OUT_EDGES  = Path("agents/ingestion/config/schema_relationships.py")


def snake_to_pascal(name: str) -> str:
    return name
    return "".join(part.capitalize() for part in name.split("_"))

def generate_nodes(node_yaml: dict) -> str:
    lines = [
        "# AUTO-GENERATED: NODE CLASSES",
        "from pydantic import BaseModel",
        "from typing import Any\n",
    ]

    for node_name, node_def in node_yaml.items():
        class_name = snake_to_pascal(node_name)

        # Generate properties class if properties exist
        props = node_def.get("properties", {})
        prop_class_name = ""
        if props:
            prop_class_name = f"{class_name}Properties"
            lines.append(f"class {prop_class_name}(BaseModel):")
            for field_name, field_info in props.items():
                type_hint = field_info.get("type", "Any")
                lines.append(indent(f"{field_name}: {type_hint}", "    "))
            lines.append("")  # newline

        # Generate main node class
        lines.append(f"class {class_name}(BaseModel):")

        # Static fields outside properties
        for key, value in node_def.items():
            if key != "properties":
                if isinstance(value, str):
                    lines.append(indent(f"{key}: str = \"{value}\"", "    "))
                else:
                    lines.append(indent(f"{key}: Any = {value}", "    "))

        # Add properties field
        if prop_class_name:
            lines.append(indent(f"properties: {prop_class_name}", "    "))

        lines.append("")  # newline

    return "\n".join(lines)

def generate_relationships(EDGE_yaml: dict) -> str:
    lines = [
        "# AUTO-GENERATED: RELATIONSHIP CLASSES",
        "from pydantic import BaseModel",
        "from typing import Any\n",
        "from .schema_nodes import *\n",
        "from typing import Optional\n"
    ]

    for rel_name, rel_def in EDGE_yaml.items():
        class_name = snake_to_pascal(rel_name)

        source = rel_def["source"]
        target = rel_def["target"]
        props = rel_def.get("properties", {})

        # Properties class (if exists)
        prop_class_name = ""
        if props:
            prop_class_name = f"{class_name}Properties"
            lines.append(f"class {prop_class_name}(BaseModel):")
            for k, v in props.items():
                type_hint = v.get("type", "Any") if isinstance(v, dict) else "Any"
                lines.append(indent(f"{k}: {type_hint}", "    "))
            lines.append("")

        # Relationship class
        lines.append(f"class {class_name}(BaseModel):")
        lines.append(indent(f"label: str = \"{rel_def['label']}\"", "    "))

        # 🔥 Always generate source + target, never derive names
        lines.append(indent(f"source: {source}", "    "))
        lines.append(indent(f"target: {target}", "    "))

        if prop_class_name:
            lines.append(indent(f"properties: {prop_class_name}", "    "))
        else:
            lines.append(indent("properties: Optional[BaseModel] = None", "    "))

        lines.append("")

    return "\n".join(lines)


def main():
    # Load YAMLs
    node_data = yaml.safe_load(NODES_YAML.read_text())
    edge_data = yaml.safe_load(EDGE_YAML.read_text())

    # Generate and write node classes
    OUT_NODES.parent.mkdir(parents=True, exist_ok=True)

    OUT_NODES.write_text(generate_nodes(node_data))
    OUT_EDGES.write_text(generate_relationships(edge_data))

    print("Generated: - generate_schema_stub.py:112")
    print(f"{OUT_NODES} - generate_schema_stub.py:113")
    print(f"{OUT_EDGES} - generate_schema_stub.py:114")


if __name__ == "__main__":
    main()
