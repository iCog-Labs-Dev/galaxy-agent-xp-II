import yaml
from pathlib import Path
from transform.node_builder import GenericNodeBuilder
import pprint
def load_schema(path="agents/ingestion/config/schema.edge.yml"):
    return yaml.safe_load(Path(path).read_text())

class GenericRelationshipBuilder:

    def __init__(
        self,
        edge_schema_path="agents/ingestion/config/schema.edge.yml",
        node_schema_path="agents/ingestion/config/schema.node.yml"
    ):
        self.schema = load_schema(edge_schema_path)
        self.node_builder = GenericNodeBuilder(node_schema_path)

    def build_edge(self, model_instance):
        """
        Accepts a relationship model instance and returns a relationship tuple
        exactly like build_node() returns a node dict.
        """
        type_name = model_instance.__class__.__name__

        if type_name not in self.schema:
            raise ValueError(f"No relationship schema found for '{type_name}'")

        schema = self.schema[type_name]

        # -----------------------------------------
        # 1. Extract source and target field values
        # -----------------------------------------
        source_model = model_instance.source
        target_model = model_instance.target

        # -----------------------------------------
        # 2. Build node dicts using GenericNodeBuilder
        # -----------------------------------------
        source_node = self.node_builder.build_node(source_model)
        target_node = self.node_builder.build_node(target_model)

        # -----------------------------------------
        # 3. Collect relationship properties
        # -----------------------------------------
        edge_props = {}
        schema_props = schema.get("properties", {})

        for prop_name in schema_props:
            # Relationship model should hold this property
            edge_props[prop_name] = getattr(model_instance, prop_name, None)

        # -----------------------------------------
        # 4. Return relationship tuple
        # -----------------------------------------
        return (
            schema["label"],

            source_node["label"],
            source_node["properties"],

            target_node["label"],
            target_node["properties"],

            edge_props
        )


