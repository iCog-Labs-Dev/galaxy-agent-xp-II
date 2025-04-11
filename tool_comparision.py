import json
import pandas as pd
import yaml
import os

# Load configuration from YAML file
CONFIG_FILE = "config.yml"
if not os.path.exists(CONFIG_FILE):
    raise FileNotFoundError(f"Configuration file '{CONFIG_FILE}' not found")

with open(CONFIG_FILE, "r") as f:
    config = yaml.safe_load(f)

# Extract file paths from config
EU_JSON_FILE = config["comparison"]["eu_json_file"]
MY_SERVER_JSON_FILE = config["comparison"]["bizon_server_json_file"]
OUTPUT_EXCEL = config["comparison"]["output_excel"]

# Load JSON files
def load_json_file(file_path):
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: '{file_path}' not found.")
        return []
    except json.JSONDecodeError:
        print(f"Error: '{file_path}' contains invalid JSON.")
        return []

print(f"Loading Galaxy EU tools from '{EU_JSON_FILE}'...")
eu_tools = load_json_file(EU_JSON_FILE)
print(f"Loading My Server tools from '{MY_SERVER_JSON_FILE}'...")
my_server_tools = load_json_file(MY_SERVER_JSON_FILE)

# Use lists to preserve all tools, keyed by name but including ID
eu_tools_list = [(tool.get("name", "Unnamed"), tool.get("id", ""), tool.get("description", "")) 
                 for tool in eu_tools if "name" in tool]
my_server_tools_list = [(tool.get("name", "Unnamed"), tool.get("id", ""), tool.get("description", "")) 
                        for tool in my_server_tools if "name" in tool]

# Combine all tools, keeping duplicates
all_tools = eu_tools_list + my_server_tools_list

# Prepare comparison data
comparison_data = {
    "Tool Name": [],
    "Tool ID": [],
    "Description": [],
    "Galaxy EU": [],
    "Galaxy My Server": []
}

print("Comparing tools by name...")
for tool_name, tool_id, tool_desc in all_tools:
    # Add every instance, no deduplication
    comparison_data["Tool Name"].append(tool_name)
    comparison_data["Tool ID"].append(tool_id)
    comparison_data["Description"].append(tool_desc)
    comparison_data["Galaxy EU"].append("✅" if (tool_name, tool_id, tool_desc) in eu_tools_list else "❌")
    comparison_data["Galaxy My Server"].append("✅" if (tool_name, tool_id, tool_desc) in my_server_tools_list else "❌")

# Create DataFrame and save to Excel
print(f"Generating Excel report '{OUTPUT_EXCEL}'...")
df = pd.DataFrame(comparison_data)
df.to_excel(OUTPUT_EXCEL, index=False, engine="openpyxl")

print(f"Comparison complete! Report saved as '{OUTPUT_EXCEL}' with {len(comparison_data['Tool Name'])} tools.")