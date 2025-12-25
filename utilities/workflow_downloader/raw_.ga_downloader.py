#!/usr/bin/env python3
import requests
import json
import os
import zipfile
import io
import time
from datetime import datetime
from pathlib import Path

# === CONFIG ===
BASE_TRS = "https://workflowhub.eu/ga4gh/trs/v2"
BASE_URL = "https://workflowhub.eu"
OUTPUT_DIR = "utilities/workflow_downloader/data"
DELAY = 0.5
TIMEOUT = 30

# ---------------------------------------------
# Add MAX_WORKFLOWS limit (None = ALL workflows)
# ---------------------------------------------
MAX_WORKFLOWS = 3    # ← change this as needed


os.makedirs(OUTPUT_DIR, exist_ok=True)

session = requests.Session()
session.headers.update({"Accept": "application/json"})

total = successful = 0



def fetch_trs(url):
    try:
        r = session.get(url, timeout=TIMEOUT)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()
    except:
        return None



def get_all_workflows():
    print("Fetching all workflows from WorkflowHub TRS...")
    workflows = []
    offset = 0
    limit = 100

    while True:
        data = fetch_trs(f"{BASE_TRS}/tools?limit={limit}&offset={offset}")
        if not data:
            break
        workflows.extend(data)
        print(f"   Got {len(data)} → total {len(workflows)}")
        if len(data) < limit:
            break
        offset += limit
        time.sleep(DELAY)

    return workflows



def is_galaxy_workflow(tool_id):
    versions = fetch_trs(f"{BASE_TRS}/tools/{tool_id}/versions")
    if not versions:
        return False
    for v in versions:
        types = [t.lower() for t in v.get("descriptor_type", []) if t]
        if any("galaxy" in t for t in types):
            return True
    return False



def extract_ga_from_rocrate(workflow_id, version_id=None):
    url = f"https://workflowhub.eu/workflows/{workflow_id}/ro_crate"
    if version_id:
        url += f"?version={version_id}"

    try:
        print(f"   Downloading RO-Crate ← {url}")
        r = session.get(url, timeout=60)
        if r.status_code != 200:
            return None

        # In-memory ZIP extraction
        zip_bytes = io.BytesIO(r.content)

        with zipfile.ZipFile(zip_bytes) as z:
            ga_files = [p for p in z.namelist() if p.endswith(".ga")]
            if not ga_files:
                return None

            ga_file = ga_files[0]
            print(f"   Found .ga inside RO-Crate: {ga_file}")

            raw_text = z.read(ga_file).decode("utf-8")

            try:
                return json.loads(raw_text)
            except:
                return {"raw_ga_text": raw_text, "file": ga_file, "source": "ro-crate"}

    except Exception as e:
        print(f"   RO-Crate extraction failed: {e}")
        return None




def main():
    global total, successful

    print(f"🔧 MAX_WORKFLOWS = {MAX_WORKFLOWS}")
    workflows = get_all_workflows()
    print(f"\nFound {len(workflows)} workflows. Scanning for Galaxy...\n")

    results = []
    processed = 0

    for wf in workflows:
        if MAX_WORKFLOWS is not None and processed >= MAX_WORKFLOWS:
            break

        total += 1
        wf_id = wf["id"]
        name = wf.get("name", "Unknown")[:100]

        print(f"[{total}/{len(workflows)}] {name} (ID: {wf_id})")

        # Descriptor-type filtering
        if not is_galaxy_workflow(wf_id):
            print("   Not a Galaxy workflow → skipping")
            time.sleep(DELAY)
            continue

        print("   GALAXY workflow detected → downloading RO-Crate...")

        ga_data = extract_ga_from_rocrate(wf_id)

        if ga_data:
            successful += 1
            processed += 1
            print("   SUCCESS! Extracted .ga")
        else:
            print("   No .ga found in RO-Crate")

        # Save result in memory
        results.append({
            "id": wf_id,
            "name": wf.get("name"),
            "page": f"https://workflowhub.eu/workflows/{wf_id}",
            "downloaded_at": datetime.now().isoformat(),
            "success": ga_data is not None,
            "workflow_ga": ga_data
        })

        print(f"   Progress: {successful}/{total} Galaxy workflows\n")
        time.sleep(DELAY)



    final_path = Path(OUTPUT_DIR) / f"workflowhub_galaxy_.ga_combined_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    # Save final combined JSON
    with open(final_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\nFINISHED!")
    print(f"   Total scanned: {total}")
    print(f"   Galaxy workflows extracted: {successful}")
    print(f"   Saved final combined JSON → {final_path}")



if __name__ == "__main__":
    main()
