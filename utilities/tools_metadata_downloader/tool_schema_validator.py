import json
import os
import glob
from jsonschema import validate, ValidationError

# Define the directory containing downloaded tool metadata
data_dir = os.path.join("utilities", "tools_metadata_downloader", "data")
schema_path = os.path.join("utilities", "tools_metadata_downloader", "schemas", "tools.schema.json")

# Ensure schema file exists
if not os.path.exists(schema_path):
    print(f"❌ Schema not found at {schema_path}")
    exit(1)

# Load the schema
with open(schema_path, "r") as f:
    schema = json.load(f)

# Find all JSON files in the data directory
json_files = glob.glob(os.path.join(data_dir, "*.json"))

if not json_files:
    print(f"❌ No JSON files found in {data_dir}")
    exit(1)

# Track validation status
failed_files = []
successful_files = []

print(f"🔍 Found {len(json_files)} JSON files. Starting validation...\n")

# Validate each file
for json_file in json_files:
    print(f"🧪 Validating: {json_file}")
    try:
        with open(json_file, "r") as f:
            data = json.load(f)
        validate(instance=data, schema=schema)
        print(f"✅ Passed: {os.path.basename(json_file)}\n")
        successful_files.append(json_file)
    except ValidationError as e:
        print(f"❌ Failed: {os.path.basename(json_file)}")
        print(f"   ↪ {e.message}\n")
        failed_files.append(json_file)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON format: {os.path.basename(json_file)}")
        print(f"   ↪ {e.msg}\n")
        failed_files.append(json_file)

# Final summary
print("✅ Validation complete.\n")
print(f"✔️ Passed: {len(successful_files)} file(s)")
print(f"❌ Failed: {len(failed_files)} file(s)")

if failed_files:
    print("\n🚨 Files with errors:")
    for f in failed_files:
        print(f" - {f}")

