import json
import os
import glob
from jsonschema import validate, ValidationError

# Step 1: Find the most recent downloaded tool file
tool_files = glob.glob("galaxy_instance_tools_*.json")
if not tool_files:
    print("❌ No tool metadata files found.")
    exit(1)

latest_file = max(tool_files, key=os.path.getmtime)
print(f"🔍 Validating latest file: {latest_file}")

# Step 2: Load JSON and schema
with open(latest_file, "r") as f:
    tools_data = json.load(f)

with open("schemas/tools.schema.json", "r") as f:
    schema = json.load(f)

# Step 3: Validate
try:
    validate(instance=tools_data, schema=schema)
    print("Validation passed: tools JSON is valid.")

    # Step 4: Prompt for valid filename to save
    valid_filename = input("💾 Enter a name to save this validated file (without extension): ").strip()
    if not valid_filename:
        print("Filename cannot be empty.")
        exit(1)

    if not valid_filename.endswith(".json"):
        valid_filename += ".json"

    # Step 5: Save to agents/data
    output_dir = os.path.join("agents", "data")
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, valid_filename)
    with open(output_path, "w") as f:
        json.dump(tools_data, f, indent=2)

    print(f"📦 Validated file saved as: {output_path}")

except ValidationError as e:
    print(f"❌ Validation failed:\n{e.message}")
