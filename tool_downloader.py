import json
import os
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from bioblend.galaxy import GalaxyInstance
from tqdm import tqdm
import requests
from dotenv import load_dotenv
import yaml

# Load environment variables from .env
load_dotenv()

# Load non-sensitive config from YAML
config_file = "config.yml"
if not os.path.exists(config_file):
    raise FileNotFoundError(f"Configuration file '{config_file}' not found")
with open(config_file, "r") as f:
    config = yaml.safe_load(f)

# Get sensitive data from .env
galaxy_url = os.getenv("GALAXY_URL")
api_key = os.getenv("GALAXY_API_KEY")

# Get non-sensitive data from YAML
output_file = config["output"]["file"]
max_workers = config["processing"]["max_workers"]
tool_limit = config["processing"].get("tool_limit", None)

# Validate sensitive data
if not galaxy_url or not api_key:
    raise ValueError("GALAXY_URL and GALAXY_API_KEY must be set in the .env file")

# Initialize Galaxy instance
gi = GalaxyInstance(url=galaxy_url, key=api_key)

# Check if cached file exists
if os.path.exists(output_file):
    print(f"Output file '{output_file}' already exists. Skipping fetch.")
else:
    print("Fetching tools from Galaxy...")
    tools = gi.tools.get_tools()
    print(f"Found {len(tools)} tools. Fetching details for all tools...")
    if tool_limit:
        tools = tools[:tool_limit]

    def fetch_tool_details(tool):
        tool_id = tool.get("id", "")
        try:
            tool_details = gi.tools.show_tool(tool_id, io_details=True)
            help_text = ""
            raw_tool_url = f"{galaxy_url}/api/tools/{tool_id}/raw_tool_source?key={api_key}"
            response = requests.get(raw_tool_url)
            response.raise_for_status()
            tool_xml = response.text
            root = ET.fromstring(tool_xml)
            help_elem = root.find("help")
            if help_elem is not None:
                help_text = help_elem.text.strip()
                print(f"Extracted help for {tool_id}: {help_text[:50]}...")
            else:
                help_text = None
                print(f"No <help> section found for {tool_id}")
            return {
                "name": tool.get("name", ""),
                "description": tool.get("description", ""),
                "category": tool.get("panel_section_name", ""),
                "help": help_text
            }
        except Exception as e:
            print(f"Error fetching details for {tool_id}: {e}")
            return None

    tools_json = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_tool = {executor.submit(fetch_tool_details, tool): tool for tool in tools}
        for future in tqdm(
            as_completed(future_to_tool),
            total=len(tools),
            desc="Processing tools",
            bar_format="{l_bar}{percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]"
        ):
            result = future.result()
            if result:
                tools_json.append(result)

    print(f"Saving results to '{output_file}'...")
    with open(output_file, "w") as f:
        json.dump(tools_json, f, indent=4)

print(f"Done! Results are saved in '{output_file}'.")