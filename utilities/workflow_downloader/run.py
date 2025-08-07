import os
import subprocess
import glob
from datetime import datetime

def run_command(cmd):
    print(f"▶ Running: {cmd}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"❌ Command failed: {cmd}")
        exit(1)
    print(f"Completed: {cmd}\n")

def get_latest_iwc_json(data_dir):
    files = glob.glob(os.path.join(data_dir, "galaxy_iwc_workflows_*.json"))
    if not files:
        print("❌ No IWC workflow JSON files found.")
        exit(1)
    latest_file = max(files, key=os.path.getmtime)
    return latest_file

if __name__ == "__main__":
    base_dir = os.path.dirname(__file__)
    data_dir = os.path.join(base_dir, "data")

    print("🚀 Starting workflow downloader → preprocessor → validator pipeline\n")

    # Step 1: Download IWC workflows
    run_command("python utilities/workflow_downloader/iwc_downloader.py")

    # Step 2: Preprocess the latest IWC workflow JSON file
    latest_file = get_latest_iwc_json(data_dir)
    run_command(f"python utilities/workflow_downloader/preprocess_wf_data.py {latest_file}")

    # Step 3: Validate all JSON files in data/ using schema
    run_command("python utilities/workflow_downloader/workflow_schema_validator.py")

    print("🎉 Pipeline completed successfully!")
