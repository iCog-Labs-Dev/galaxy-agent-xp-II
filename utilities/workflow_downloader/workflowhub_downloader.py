# ============================================================================================To run use :  python utilities/workflow_downloader/workflowhub_downloader.py ============================================================================================
#
import requests
import json
import os
from datetime import datetime
from unstructured.partition.text import partition_text
import re

# ---------------------------------------------
# CONFIG (developer can change MAX_WORKFLOWS)
# ---------------------------------------------
MAX_WORKFLOWS = None  # Set None for ALL workflows


# clean readme content helper
def clean_readme(text):
    elements = partition_text(text=text)

    cleaned = []
    for el in elements:
        content = el.text.strip()
        if not content:
            continue

        # Remove literal "\n" sequences (e.g. backslash + n) and any surrounding spaces
        content = re.sub(r'\s*\\n\s*', ' ', content)
        # Replace real newlines/carriage returns with a single space
        content = re.sub(r'[\r\n]+', ' ', content)
        # Collapse multiple spaces into one and trim
        content = re.sub(r'\s+', ' ', content).strip()

        if len(content) < 5:
            continue

        low = content.lower()

        if any(k in low for k in [
            "click and drag",
            "double click",
            "views:",
            "downloads:",
            "runs:",
            "activity",
            "version history",
            "tags",
            "attributions",
            "added/updated"
        ]):
            continue

        cleaned.append(content)

    return ' '.join(cleaned)


# ---------------------------------------------
# Fetch ALL workflow IDs from WorkflowHub
# ---------------------------------------------
def fetch_all_workflow_ids():
    print("Fetching workflow catalog from WorkflowHub...")

    url = "https://workflowhub.eu/workflows.json"

    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        json_data = resp.json()
        workflows = json_data.get("data", [])
    except Exception as e:
        print(f"Failed to fetch workflow catalog: {e}")
        return []

    ids = []
    for wf in workflows:
        try:
            wf_id = int(wf.get("id"))
            ids.append(wf_id)
        except:
            continue

    ids = sorted(ids)

    print(f"Found {len(ids)} workflow entries in WorkflowHub")
    print(f"Sorted first 10 workflow IDs: {ids[:10]}")

    return ids


# ---------------------------------------------
# GALAXY DESCRIPTOR FILTER
# ---------------------------------------------
def is_galaxy_descriptor(wf_id):
    """
    Checks TRS versions to determine whether this workflow
    has any GALAXY descriptor types.
    """
    versions_url = f"https://workflowhub.eu/ga4gh/trs/v2/tools/{wf_id}/versions"

    try:
        resp = requests.get(versions_url, timeout=20)
        resp.raise_for_status()
        versions = resp.json()
    except Exception:
        return False

    for version in versions:
        desc_list = version.get("descriptor_type", [])
        desc_list = [d.lower() for d in desc_list if d]

        # Key condition → must contain GALAXY descriptor
        if any("galaxy" in d for d in desc_list):
            return True

    return False


# ---------------------------------------------
# Helper: Fetch TRS Metadata
# ---------------------------------------------
def fetch_trs_metadata(wf_id):
    trs_url = f"https://workflowhub.eu/ga4gh/trs/v2/tools/{wf_id}"
    resp = requests.get(trs_url, timeout=25)
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------
# Parse GA File (reusing your old logic)
# ---------------------------------------------
def parse_ga_file(ga_json):
    try:
        workflow_name = ga_json.get("name", "")
        steps = ga_json.get("steps", {})

        step_list = []
        subworkflows = []
        step_data: dict
        step_id: str
        
        for step_id, step_data in steps.items():
            
            step_type = step_data.get("type", "")
             
            step_list.append({
                "step_id": int(step_id),
                "annotation": step_data.get("annotation", ""),
                "type": step_type,
                "tool_id": step_data.get("tool_id"),
                "tool_version": step_data.get("tool_version"),
                "name": step_data.get("name", ""),
                "subworkflow_name": step_data.get("subworkflow").get("name") if step_data.get("subworkflow", "") else "",
                "label": step_data.get("label", ""),
                "inputs": step_data.get("inputs", []),
                "outputs": step_data.get("outputs", []),
                "input_connections": step_data.get("input_connections", {}),
                "tool_shed_repository": step_data.get("tool_shed_repository", {})
            })
            
        if step_type == "subworkflow" and "subworkflow" in step_data:

                subwf_json = step_data["subworkflow"]
                parsed_sub = parse_ga_file(subwf_json)

                if parsed_sub:
                    subworkflows.append(parsed_sub)

        return {
            "workflow_name": workflow_name,
            "number_of_steps": len(steps),
            "steps": step_list,
            "subworkflows": subworkflows
        }

    except Exception as e:
        print("Error parsing GA file:", e)
        return None


# ---------------------------------------------
# Build Old-IWC-Compatible Output from WorkflowHub
# ---------------------------------------------
def process_workflowhub_workflow(wf_id):

    # STEP 1: TRS metadata
    try:
        trs = fetch_trs_metadata(wf_id)
    except Exception as e:
        print(f"TRS metadata fetch failed for {wf_id}: {e}")
        return None

    # Category mapping → organization.lower()
    org_raw = trs.get("organization")
    if isinstance(org_raw, dict):
        org = org_raw.get("name", "")
    elif isinstance(org_raw, str):
        org = org_raw
    else:
        org = "workflowhub"

    category = org.lower() if org else "workflowhub"

    # workflow_repository mapping → TRS.name slugified
    repo_name = trs.get("name", "").replace(" ", "_").lower()

    # STEP 2: Fetch versions to find the latest
    versions_url = f"https://workflowhub.eu/ga4gh/trs/v2/tools/{wf_id}/versions"
    try:
        resp = requests.get(versions_url, timeout=20)
        resp.raise_for_status()
        versions = resp.json()
    except Exception as e:
        print(f"Failed to fetch versions for {wf_id}: {e}")
        return None

    if not versions:
        print(f"No versions found for {wf_id}")
        return None

    # Find latest version ID (assuming IDs are numeric strings, take max)
    try:
        latest_version = max(versions, key=lambda v: int(v['id']))['id']
    except ValueError:
        print(f"Unable to determine latest version for {wf_id}")
        return None

    # STEP 3: Fetch GALAXY files to find primary descriptor path (file_name)
    files_url = f"https://workflowhub.eu/ga4gh/trs/v2/tools/{wf_id}/versions/{latest_version}/GALAXY/files"
    try:
        resp = requests.get(files_url, timeout=20)
        resp.raise_for_status()
        files = resp.json()
    except Exception as e:
        print(f"Failed to fetch files for {wf_id} version {latest_version}: {e}")
        return None

    primary = next((f for f in files if f['file_type'] == 'PRIMARY_DESCRIPTOR'), None)
    if not primary:
        print(f"No primary GA descriptor found for {wf_id} version {latest_version}")
        return None

    file_name = primary['path']

    # STEP 4: Construct the direct .ga download URL
    raw_download_url = f"https://workflowhub.eu/workflows/{wf_id}/git/{latest_version}/download/{file_name}"

    # STEP 5: Download the .ga file directly
    try:
        resp = requests.get(raw_download_url, timeout=30)
        resp.raise_for_status()
        ga_json = json.loads(resp.text)
    except Exception as e:
        print(f"Failed to download .ga from {raw_download_url}: {e}")
        return None

    # STEP 6: parse GA
    parsed = parse_ga_file(ga_json)
    if parsed is None:
        return None

    # Tools extraction
    # tools_used = []
    # steps = ga_json.get("steps", {})

    # for sid, step in steps.items():
    #     tools_used.append({
    #         "id": step.get("tool_id", "unknown"),
    #         "name": step.get("name", "unknown"),
    #         "version": step.get("tool_version", "unknown"),
    #         "owner": step.get("tool_shed_repository", {}).get("owner", "unknown"),
    #         "category": step.get("type", "unknown"),
    #         "tool_shed_url": step.get("tool_shed_repository", {}).get("url", "")
    #     })
    if parsed:
        subworkflows = parsed.get("subworkflows", [])
        parsed.pop("subworkflows")
        workflow_files = [parsed]
        workflow_files.extend(subworkflows)
        
        parsed.update({
            "file_name": file_name,
            "raw_download_url": raw_download_url,
            # "tools_used": tools_used
        })

    # Use TRS description as readme_content (with cleaning)
    raw_description = trs.get("description", "") or ""
    readme_content = clean_readme(raw_description)
    print(f"Cleaned README content for {wf_id}:\n{readme_content}")

    # FINAL: Legacy Schema Output
    return {
        "category": category.lower(),
        "workflow_repository": repo_name.lower(),
        "workflow_files": workflow_files,
        "readme_content": readme_content,
    }


# ---------------------------------------------
# MAIN RUNNER
# ---------------------------------------------
def main():
    print("Starting WorkflowHub Downloader...")

    all_ids = fetch_all_workflow_ids()
    if not all_ids:
        print("No workflow IDs found. Exiting.")
        return

    all_data = []
    processed = 0

    print(f"MAX_WORKFLOWS = {MAX_WORKFLOWS}")

    for wf_id in all_ids:

        if MAX_WORKFLOWS is not None and processed >= MAX_WORKFLOWS:
            break

        print(f"\nProcessing WorkflowHub ID: {wf_id}")

        if not is_galaxy_descriptor(wf_id):
            print("Not a GALAXY workflow → skipping")
            continue

        print("GALAXY descriptor detected → downloading...")

        entry = process_workflowhub_workflow(wf_id)
        if entry:
            all_data.append(entry)
            processed += 1

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(out_dir, exist_ok=True)

    output_file = os.path.join(out_dir, f"iwc_full_{timestamp}.json")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)

    print(f"\nSuccessfully saved {processed} cleaned workflows → {output_file}")


if __name__ == "__main__":
    main()