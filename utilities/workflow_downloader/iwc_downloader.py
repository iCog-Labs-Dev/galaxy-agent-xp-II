import requests
import json
import os
import zipfile
import io
from datetime import datetime


# ---------------------------------------------
# CONFIG (developer can change MAX_WORKFLOWS)
# ---------------------------------------------
MAX_WORKFLOWS = None  # Set None for ALL workflows


# ---------------------------------------------
# Fetch ALL workflow IDs from WorkflowHub
# ---------------------------------------------
def fetch_all_workflow_ids():
    print("🔍 Fetching workflow catalog from WorkflowHub...")

    url = "https://workflowhub.eu/workflows.json"

    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        json_data = resp.json()
        workflows = json_data.get("data", [])
    except Exception as e:
        print(f"❌ Failed to fetch workflow catalog: {e}")
        return []

    ids = []
    for wf in workflows:
        try:
            wf_id = int(wf.get("id"))
            ids.append(wf_id)
        except:
            continue

    ids = sorted(ids)

    print(f"📦 Found {len(ids)} workflow entries in WorkflowHub")
    print(f"➡️ Sorted first 10 workflow IDs: {ids[:10]}")

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
# Helper: download ROCrate ZIP and extract .ga
# ---------------------------------------------
def extract_ga_from_zip(zip_bytes):
    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
            for file in z.namelist():
                if file.endswith(".ga"):
                    raw = z.read(file).decode("utf-8")
                    return file, json.loads(raw)
    except Exception as e:
        print(f"❌ Failed to extract GA file: {e}")
    return None, None


# ---------------------------------------------
# Parse GA File (reusing your old logic)
# ---------------------------------------------
def parse_ga_file(ga_json):
    try:
        workflow_name = ga_json.get("name", "")
        steps = ga_json.get("steps", {})

        step_list = []
        for step_id, step_data in steps.items():
            step_list.append({
                "step_id": int(step_id),
                "annotation": step_data.get("annotation", ""),
                "type": step_data.get("type", ""),
                "tool_id": step_data.get("tool_id"),
                "tool_version": step_data.get("tool_version"),
                "name": step_data.get("name", ""),

                "inputs": step_data.get("inputs", []),
                "outputs": step_data.get("outputs", []),
                "input_connections": step_data.get("input_connections", {}),

                "tool_shed_repository": step_data.get("tool_shed_repository", {})
            })

        return {
            "workflow_name": workflow_name,
            "number_of_steps": len(steps),
            "steps": step_list
        }

    except Exception as e:
        print("❌ Error parsing GA file:", e)
        return None


# ---------------------------------------------
# Build Old-IWC-Compatible Output from WorkflowHub
# ---------------------------------------------
def process_workflowhub_workflow(wf_id):

    # STEP 1: TRS metadata
    try:
        trs = fetch_trs_metadata(wf_id)
    except Exception as e:
        print(f"❌ TRS metadata fetch failed for {wf_id}: {e}")
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

    # STEP 2: download ROCrate
    crate_url = f"https://workflowhub.eu/workflows/{wf_id}/download?format=rocrate"

    try:
        zip_resp = requests.get(crate_url, timeout=30)
        zip_resp.raise_for_status()
    except Exception as e:
        print(f"❌ ROCrate download failed for {wf_id}: {e}")
        return None

    # STEP 3: extract GA file
    file_name, ga_json = extract_ga_from_zip(zip_resp.content)
    if ga_json is None:
        print(f"⚠️ No GA file found for workflow ID {wf_id}")
        return None

    # STEP 4: parse GA
    parsed = parse_ga_file(ga_json)
    if parsed is None:
        return None

    # Tools extraction
    tools_used = []
    steps = ga_json.get("steps", {})

    for sid, step in steps.items():
        tools_used.append({
            "id": step.get("tool_id", "unknown"),
            "name": step.get("name", "unknown"),
            "version": step.get("tool_version", "unknown"),
            "owner": step.get("tool_shed_repository", {}).get("owner", "unknown"),
            "category": step.get("type", "unknown"),
            "tool_shed_url": step.get("tool_shed_repository", {}).get("url", "")
        })

    parsed.update({
        "file_name": file_name,
        "raw_download_url": crate_url,
        "tools_used": tools_used
    })

    # TRS.description as readme_content
    description = trs.get("description", "") or ""
    has_readme = bool(description.strip())

    # FINAL: Legacy Schema Output
    return {
        "category": category,
        "workflow_repository": repo_name,
        "workflow_files": [parsed],
        "has_test_data": False,
        "has_dockstore_yml": False,
        "has_changelog": False,
        "has_readme": has_readme,
        "readme_content": description.lower(),
        "planemo_tests": []
    }


# ---------------------------------------------
# MAIN RUNNER
# ---------------------------------------------
def main():
    print("🚀 Starting WorkflowHub Downloader...")

    all_ids = fetch_all_workflow_ids()
    if not all_ids:
        print("❌ No workflow IDs found. Exiting.")
        return

    all_data = []
    processed = 0

    print(f"🔧 MAX_WORKFLOWS = {MAX_WORKFLOWS}")

    for wf_id in all_ids:

        if MAX_WORKFLOWS is not None and processed >= MAX_WORKFLOWS:
            break

        print(f"\n📦 Processing WorkflowHub ID: {wf_id}")

        # -------------------------------------
        # 🚨 NEW: Check Galaxy descriptor type
        # -------------------------------------
        if not is_galaxy_descriptor(wf_id):
            print("⏭️  Not a GALAXY workflow → skipping")
            continue

        print("✅ GALAXY descriptor detected → downloading...")

        entry = process_workflowhub_workflow(wf_id)
        if entry:
            all_data.append(entry)
            processed += 1

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(out_dir, exist_ok=True)

    output_file = os.path.join(out_dir, f"workflowhub_cleaned_{timestamp}.json")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Successfully saved {processed} cleaned workflows → {output_file}")


if __name__ == "__main__":
    main()
