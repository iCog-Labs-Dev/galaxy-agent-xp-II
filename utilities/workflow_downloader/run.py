import os
import json
import subprocess
import glob

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
    run_command("python utilities/workflow_downloader/workflowhub_downloader.py")
    
    output_file = os.path.join(base_dir, f"final_combined.json") 

    # Load existing IWC workflows
    iwc_file = os.path.join(base_dir, f"iwc_full.json")
    if os.path.exists(iwc_file) and os.path.getsize(iwc_file) > 0:
        with open(iwc_file, "r", encoding="utf-8") as f:
            iwc = json.load(f)
    else:
        iwc = []

    # Load WorkflowHub workflows
    workflow_hub_file = os.path.join(data_dir, "workflowhub_full.json")
    if os.path.exists(workflow_hub_file) and os.path.getsize(workflow_hub_file) > 0:
        with open(workflow_hub_file, "r", encoding="utf-8") as f:
            workflow_hub = json.load(f)
    else:
        workflow_hub = []

    # Build set of existing workflow keys to filter duplicates
    existing_keys = set()
    for entry in iwc:
        for wf in entry.get("workflow_files", []):
            key = wf.get("raw_download_url") or (wf.get("workflow_name"), wf.get("file_name"))
            existing_keys.add(key)

    # Filter WorkflowHub workflows to only add new unique entries
    new_entries = []
    for entry in workflow_hub:
        filtered_entry = entry.copy()
        filtered_wfs = []
        for wf in entry.get("workflow_files", []):
            key = wf.get("raw_download_url") or (wf.get("workflow_name"), wf.get("file_name"))
            if key not in existing_keys:
                filtered_wfs.append(wf)
                existing_keys.add(key)
        filtered_entry["workflow_files"] = filtered_wfs
        if filtered_wfs:
            new_entries.append(filtered_entry)

    # Merge new unique entries
    iwc.extend(new_entries)

    # Write updated dataset
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(iwc, f, indent=2, ensure_ascii=False)

    # # Step 2: Preprocess the latest IWC workflow JSON file
    # latest_file = get_latest_iwc_json(data_dir)
    # run_command(f'python utilities/workflow_downloader/preprocess_wf_data.py "{latest_file}"')
    # # Step 3: Validate all JSON files in data/ using schema
    # run_command("python utilities/workflow_downloader/workflow_schema_validator.py")

    print("🎉 Pipeline completed successfully!")
