import json
import os
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from bioblend.galaxy import GalaxyInstance
from tqdm import tqdm
import requests
from dotenv import load_dotenv
import yaml
import random
from datetime import datetime

# Load environment variables from .env
load_dotenv()

# Load config from YAML
config_file = "config.yml"
if not os.path.exists(config_file):
    raise FileNotFoundError(f"Configuration file '{config_file}' not found")
with open(config_file, "r") as f:
    config = yaml.safe_load(f)

# Get sensitive info from environment
galaxy_url = os.getenv("GALAXY_URL")
api_key = os.getenv("GALAXY_API_KEY")

if not galaxy_url or not api_key:
    raise ValueError("GALAXY_URL and GALAXY_API_KEY must be set in the .env file")

# Get non-sensitive config values
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
output_file = f"utilities/tools_metadata_downloader/data/galaxy_instance_tools_{timestamp}.json"
max_workers = config["processing"]["max_workers"]
tool_limit = config["processing"].get("tool_limit", None)
categories_config = config.get("categories", {})

# Connect to Galaxy
gi = GalaxyInstance(url=galaxy_url, key=api_key)

if os.path.exists(output_file):
    print(f"Output file '{output_file}' already exists. Skipping fetch.")
else:
    print("Fetching tools from Galaxy...")
    tools = gi.tools.get_tools()
    print(f"Found {len(tools)} tools.")

    # Group tools by category
    tools_by_category = {}
    for tool in tools:
        category = tool.get("panel_section_name", "Uncategorized")
        tools_by_category.setdefault(category, []).append(tool)

    # Deduplicate and sample tools by category
    tool_map = {}
    for category, cat_tools in tools_by_category.items():
        percentage = categories_config.get(category, {}).get("percentage", 1)
        if not isinstance(percentage, (int, float)) or percentage < 0:
            print(f"Invalid percentage for {category}: {percentage}. Using 100%.")
            percentage = 1
        percentage = min(percentage, 1)
        num_tools = int(len(cat_tools) * percentage)
        if num_tools == 0 and percentage > 0:
            num_tools = 1

        print(f"Selecting {num_tools} of {len(cat_tools)} tools from {category} ({percentage*100:.1f}%)")
        selected_tools = random.sample(cat_tools, num_tools) if num_tools < len(cat_tools) else cat_tools

        for tool in selected_tools:
            tool_id = tool.get("id")
            if not tool_id:
                continue
            if tool_id not in tool_map:
                tool_map[tool_id] = {"base": tool, "categories": set()}
            tool_map[tool_id]["categories"].add(category)

    # Final filtered list
    filtered_tools = []
    for entry in tool_map.values():
        tool = entry["base"]
        tool["categories"] = list(entry["categories"])
        filtered_tools.append(tool)
    if tool_limit:
        filtered_tools = filtered_tools[:tool_limit]

    print(f"Fetching details for {len(filtered_tools)} tools...")

    def fetch_tool_details(tool: dict) -> dict | None:
        tool_id = tool.get("id", "")
        try:
            # Get tool details
            tool_details = gi.tools.show_tool(tool_id, io_details=True)

            help_text = ""
            raw_tool_url = f"{galaxy_url}/api/tools/{tool_id}/raw_tool_source?key={api_key}"
            response = requests.get(raw_tool_url)
            response.raise_for_status()
            tool_xml = response.text

            root = ET.fromstring(tool_xml)
            help_elem = root.find("help")
            if help_elem is not None and help_elem.text:
                help_text = help_elem.text.strip()
                print(f"Extracted help for {tool_id}: {help_text[:50]}...")
            else:
                print(f"No <help> section found for {tool_id}")

            # Use the original tool_id as it should already be in the correct format
            # For ToolShed tools, the id should already be in format: 
            # toolshed.g2.bx.psu.edu/repos/owner/repo/tool_id/version
            # For local tools, it will remain as the local ID
            
            # Return only the requested keys in the specified order
            return {
                "id": tool_id,  # This should already be in the correct format
                "name": tool.get("name", ""),
                "description": tool.get("description", ""),
                "categories": tool.get("categories", []),
                "version": tool.get("version", ""),
                "help": help_text
            }
        except Exception as e:
            print(f"Error fetching details for {tool_id}: {e}")
            return None

    tools_json = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_tool = {executor.submit(fetch_tool_details, tool): tool for tool in filtered_tools}
        for future in tqdm(
            as_completed(future_to_tool),
            total=len(filtered_tools),
            desc="Processing tools",
            bar_format="{l_bar}{percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]"
        ):
            result = future.result()
            if result:
                tools_json.append(result)

    print(f"Saving {len(tools_json)} tools to '{output_file}'...")
    with open(output_file, "w") as f:
        json.dump(tools_json, f, indent=4)

print(f"✅ Done! Results are saved in '{output_file}'.")