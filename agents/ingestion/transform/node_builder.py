import yaml
import uuid
import hashlib
from pathlib import Path

def load_node_schema(path="agents/ingestion/config/schema.node.yml"):
    return yaml.safe_load(Path(path).read_text())


class GenericNodeBuilder:
    
    def __init__(self, schema_path="agents/ingestion/config/schema.node.yml"):
        self.schema = load_node_schema(schema_path)
        
    def _generate_id(self, *args):
        if not args:  # no arguments, fallback to UUID
            return str(uuid.uuid4())
        s = "_".join([str(a) for a in args if a is not None])
        return hashlib.md5(s.encode("utf-8")).hexdigest()

    def build_node(self, model_instance):
        type_name = model_instance.__class__.__name__

        if type_name not in self.schema:
            raise ValueError(f"No node schema found for '{type_name}'")

        schema = self.schema[type_name]
        node = model_instance.model_dump()
        
            # Flatten nested 'properties' key if exists
        if "properties" in node and isinstance(node["properties"], dict):
            node.update(node.pop("properties"))

        # get unique fields from schema
        unique_fields = schema.get("unique_key", [])
        # if not unique_fields:
        #     raise ValueError(f"No unique_key defined for {type_name}")
        
        # generate ID
        unique_values = [node.get(f) for f in unique_fields]
        # Always inject as "id"
        node["id"] = self._generate_id(*unique_values)

        label = node["label"]
        del node["label"]


        return {
            "type": type_name,
            "label": label,
            "properties": node
        }
