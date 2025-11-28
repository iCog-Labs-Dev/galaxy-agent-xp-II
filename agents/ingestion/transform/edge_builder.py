import yaml
from pathlib import Path

def load_relationship_schema(path=".edge.yml"):
    return yaml.safe_load(Path(path).read_text())

class GenericRelationshipBuilder:

    def __init__(self, schema_path="agents/ingestion/config/schema.relationship.yml"):
        self.schema = load_relationship_schema(schema_path)
        
                
    def _generate_id(self, *args):
        import hashlib
        s = "_".join([str(a) for a in args if a is not None])
        return hashlib.md5(s.encode("utf-8")).hexdigest()

    def build_edge(self, model_instance):
        type_name = model_instance.__class__.__name__

        if type_name not in self.schema:
            raise ValueError(f"No schema found for type '{type_name}'")

        schema = self.schema[type_name]
        node = model_instance.model_dump()
        
            # Flatten nested 'properties' key if exists
        if "properties" in node and isinstance(node["properties"], dict):
            node.update(node.pop("properties"))

        # get unique fields from schema
        unique_fields = schema.get("unique_key", [])
        if not unique_fields:
            raise ValueError(f"No unique_key defined for {type_name}")
        
        label = node["label"]
        del node["label"]
        # generate ID
        unique_values = [node.get(f) for f in unique_fields]
        # Always inject as "id"
        node["id"] = self._generate_id(*unique_values)

        return {
            "type": type_name,
            "label": label,
            "properties": node
        }


