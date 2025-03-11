from bioblend.galaxy import GalaxyInstance
import json
import os
import dotenv

# Load environment variables from .env file
dotenv.load_dotenv()

# Get Galaxy URL and API key from environment variables
galaxy_url = os.getenv("GALAXY_URL")
api_key = os.getenv("GALAXY_API_KEY")

# Validate that both are present
if not galaxy_url or not api_key:
    raise ValueError("GALAXY_URL and GALAXY_API_KEY must be set in the .env file")

# Initialize Galaxy instance
gi = GalaxyInstance(url=galaxy_url, key=api_key)

# Fetch tools from Galaxy
tools = gi.tools.get_tools()

# Extract relevant tool info
tools_json = [
    {
        "name": tool.get("name", ""),
        "description": tool.get("description", ""),
        "category": tool.get("panel_section_name", ""),
        "help": ""  
    }
    for tool in tools
]

# Print the tools as pretty JSON
print(json.dumps(tools_json, indent=4))
