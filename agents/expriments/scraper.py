from bioblend.galaxy import GalaxyInstance
import csv
from datetime import datetime
from pathlib import Path

# ========================= CONFIG =========================
URL = "https://usegalaxy.org/"
API_KEY = "bcdfedaffa33cc26f876f4e8ecbe2815"

# Set to None for ALL workflows (~2285), or a number for testing
MAX_WORKFLOWS = None       # ← Change this as needed
OUTPUT_BASENAME = "usegalaxy_workflow_connections"
# =========================================================

gi = GalaxyInstance(url=URL, key=API_KEY)

output_dir = Path(__file__).resolve().parent / "data"
output_dir.mkdir(parents=True, exist_ok=True)
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
output_path = output_dir / f"{OUTPUT_BASENAME}_{timestamp}.tsv"

print("Fetching list of published workflows...")
published_wfs = gi.workflows.get_workflows(published=True)
print(f"Found {len(published_wfs)} published workflows.")

# We will write 8 columns only (no flags)
columns = [
    "workflow_id",
    "created_at",
    "source_step_id",
    "source_tool",
    "source_tool_version",
    "target_step_id",
    "target_tool",
    "target_tool_version"
]

with open(output_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f, delimiter='\t')   # tab-separated → matches your notebook
    writer.writerow(columns)

    processed = 0

    for wf_info in published_wfs:
        if MAX_WORKFLOWS is not None and processed >= MAX_WORKFLOWS:
            break

        wf_id = wf_info['id']
        created_at = wf_info.get('create_time', '')   # Galaxy returns ISO datetime

        try:
            wf = gi.workflows.export_workflow_dict(wf_id)
            steps = wf.get('steps', {})

            for step_id, step in steps.items():
                target_tool = step.get('tool_id') or "Input"
                target_tool_version = step.get('tool_version', '')

                connections = step.get('input_connections', {})

                for input_name, conn in connections.items():
                    conn_list = conn if isinstance(conn, list) else [conn]

                    for c in conn_list:
                        source_step_id = str(c.get('id', ''))
                        source_step = steps.get(source_step_id, {})

                        source_tool = source_step.get('tool_id') or "Input"
                        source_tool_version = source_step.get('tool_version', '')

                        writer.writerow([
                            wf_id,
                            created_at,
                            source_step_id,
                            source_tool,
                            source_tool_version,
                            step_id,
                            target_tool,
                            target_tool_version
                        ])

            processed += 1
            print(f"✓ Processed {processed}/{min(MAX_WORKFLOWS or len(published_wfs), len(published_wfs))} → {wf_info.get('name', wf_id)}")

        except Exception as e:
            print(f"✗ Skipped {wf_id}: {e}")

print(f"\nDone! Saved to → {output_path}")
print(f"Total workflows processed: {processed}")
