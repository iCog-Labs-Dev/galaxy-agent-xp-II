import json
from jsonschema import validate, ValidationError
import os

def load_schema(schema_file_path):
    with open(schema_file_path) as f:
        return json.load(f)

def validate_json_file(json_file_path, schema_file_path):
    with open(json_file_path) as f:
        data = json.load(f)
    schema = load_schema(schema_file_path)

    try:
        validate(instance=data, schema=schema)
        print(f"✅ Validation passed for: {json_file_path}")
    except ValidationError as e:
        print(f"❌ Validation failed for: {json_file_path}")
        print(f"  -> {e.message}")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(__file__))
    data_dir = os.path.join(base_dir, "data")
    schema_dir = os.path.join(base_dir, "schemas")

    json_file_path = os.path.join(data_dir, "iwc_workflows_summary.json")
    schema_file_path = os.path.join(schema_dir, "gtn-workflow-validator.schema.json")

    validate_json_file(json_file_path, schema_file_path)
