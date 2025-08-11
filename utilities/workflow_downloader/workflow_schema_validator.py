import os
import json
import glob
from jsonschema import validate, ValidationError

# --- Config ---
SCHEMA_MAP = {
    "galaxy_iwc_workflows_": "iwc_downloaded.schema.json",
    "preprocessed_workflows_": "preprocessed-workflows.schema.json"
}

def load_schema(schema_path):
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)

def detect_schema(file_name, schema_dir):
    for prefix, schema_file in SCHEMA_MAP.items():
        if file_name.startswith(prefix):
            return os.path.join(schema_dir, schema_file)
    return None

def validate_file(json_file_path, schema_path):
    try:
        with open(json_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        schema = load_schema(schema_path)
        validate(instance=data, schema=schema)
        print(f"✅ Passed: {os.path.basename(json_file_path)}")
        return True
    except ValidationError as e:
        print(f"❌ Failed: {os.path.basename(json_file_path)}")
        print(f"   ↪ {e.message}")
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {os.path.basename(json_file_path)}")
        print(f"   ↪ {e.msg}")
    return False

def validate_all(data_dir, schema_dir):
    json_files = glob.glob(os.path.join(data_dir, "*.json"))
    if not json_files:
        print("🚫 No JSON files found.")
        return

    passed, failed = 0, 0
    print(f"🔍 Validating {len(json_files)} JSON files...\n")

    for json_file in json_files:
        file_name = os.path.basename(json_file)
        schema_path = detect_schema(file_name, schema_dir)

        if not schema_path or not os.path.exists(schema_path):
            print(f"⚠️ Skipped: {file_name} (no matching schema)")
            continue

        if validate_file(json_file, schema_path):
            passed += 1
        else:
            failed += 1

    print("\n✅ Done!")
    print(f"✔️ Passed: {passed}")
    print(f"❌ Failed: {failed}")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(__file__))
    data_dir = os.path.join(base_dir, "workflow_downloader", "data")
    schema_dir = os.path.join(base_dir, "workflow_downloader", "schemas")
    validate_all(data_dir, schema_dir)