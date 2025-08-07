import subprocess
import glob
import os
from datetime import datetime

# Constants
DATA_DIR = "utilities/tools_metadata_downloader/data"
PREPROCESS_SCRIPT = "utilities/tools_metadata_downloader/preprocess_data.py"
SCHEMA_VALIDATOR_SCRIPT = "utilities/tools_metadata_downloader/tool_schema_validator.py"
DOWNLOADER_SCRIPT = "utilities/tools_metadata_downloader/tool_downloader.py"

def run_downloader():
    print("\n🚀 Running Tool Downloader...")
    subprocess.run(["python", DOWNLOADER_SCRIPT], check=True)

def get_latest_tool_file():
    print("\n🔍 Looking for latest downloaded tool metadata file...")
    files = glob.glob(os.path.join(DATA_DIR, "galaxy_instance_tools_*.json"))
    if not files:
        raise FileNotFoundError("❌ No tool metadata JSON files found.")
    latest = max(files, key=os.path.getmtime)
    print(f"✅ Found latest file: {latest}")
    return latest

def run_preprocessor(latest_file):
    print("\n🧹 Running Preprocessor on latest file...")
    subprocess.run(["python", PREPROCESS_SCRIPT, latest_file], check=True)

def run_validator():
    print("\n🧪 Running Schema Validator...")
    subprocess.run(["python", SCHEMA_VALIDATOR_SCRIPT], check=True)

def main():
    start = datetime.now()
    print("🛠️ Starting full tool metadata pipeline...\n")

    try:
        run_downloader()
        latest_file = get_latest_tool_file()
        run_preprocessor(latest_file)
        run_validator()
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        return

    duration = datetime.now() - start
    print(f"\n✅ Pipeline completed successfully in {duration}.")

if __name__ == "__main__":
    main()
