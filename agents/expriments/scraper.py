import csv
import concurrent.futures
from datetime import datetime
from pathlib import Path
from bioblend.galaxy import GalaxyInstance

# ========================= CONFIG =========================
URL = "https://usegalaxy.org/"
API_KEY = "bcdfedaffa33cc26f876f4e8ecbe2815"  # Ensure this is valid/safe

# Set to None for ALL workflows, or a number for testing
MAX_WORKFLOWS = None     
MAX_WORKERS = 5         
OUTPUT_BASENAME = "usegalaxy_workflow_connections"
# =========================================================

gi = GalaxyInstance(url=URL, key=API_KEY)

def process_workflow(wf_info):
    """
    Fetches details for a single workflow and extracts connections.
    Returns a list of rows (tuples) to write to CSV.
    """
    wf_id = wf_info['id']
    wf_name = wf_info.get('name', wf_id)
    created_at = wf_info.get('create_time', '')
    
    rows = []

    try:
        # Fetch the full workflow details
        wf = gi.workflows.export_workflow_dict(wf_id)
        steps = wf.get('steps', {})

        for step_id, step in steps.items():
            # --- TARGET (Consumer) ---
            target_step_id = step_id
            target_tool = step.get('tool_id') or "Input"
            target_tool_version = step.get('tool_version', '')
            
            # Input connections: key = input name on target, value = source details
            connections = step.get('input_connections', {})

            for target_input_name, conn in connections.items():
                conn_list = conn if isinstance(conn, list) else [conn]

                for c in conn_list:
                    # --- SOURCE (Producer) ---
                    source_step_id = str(c.get('id', ''))
                    source_step = steps.get(source_step_id, {})

                    source_tool = source_step.get('tool_id') or "Input"
                    source_tool_version = source_step.get('tool_version', '')
                    
                    source_output_name = c.get('output_name', 'output')

                    rows.append((
                        wf_id,
                        wf_name,            # ← Added wf_name here
                        created_at,
                        source_step_id,
                        source_tool,
                        source_tool_version,
                        source_output_name,
                        target_step_id,
                        target_tool,
                        target_tool_version,
                        target_input_name
                    ))
        return rows, None

    except Exception as e:
        return [], f"Error processing {wf_id} ({wf_name}): {e}"

def main():
    # Setup Output
    output_dir = Path(__file__).resolve().parent / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_path = output_dir / f"{OUTPUT_BASENAME}_{timestamp}.tsv"

    print("Fetching list of published workflows...")
    try:
        # Note: If fetching all 2k+, consider adding limit/offset as discussed before
        published_wfs = gi.workflows.get_workflows(published=True)
    except Exception as e:
        print(f"Failed to fetch workflows: {e}")
        return

    if MAX_WORKFLOWS:
        published_wfs = published_wfs[:MAX_WORKFLOWS]
        
    print(f"Found {len(published_wfs)} workflows. Starting parallel processing with {MAX_WORKERS} workers...")

    # Column Headers
    columns = [
        "workflow_id", 
        "workflow_name",      # ← Added header
        "created_at",
        "source_step_id", "source_tool", "source_tool_version", "source_output_name",
        "target_step_id", "target_tool", "target_tool_version", "target_input_name"
    ]

    total_connections = 0
    errors = []

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(columns)

        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_wf = {executor.submit(process_workflow, wf): wf for wf in published_wfs}
            
            for i, future in enumerate(concurrent.futures.as_completed(future_to_wf), 1):
                wf = future_to_wf[future]
                rows, error = future.result()
                
                if error:
                    errors.append(error)
                    print(f"[{i}/{len(published_wfs)}] ✗ {error}")
                else:
                    if rows:
                        writer.writerows(rows)
                        total_connections += len(rows)
                    print(f"[{i}/{len(published_wfs)}] ✓ {wf.get('name', 'Unknown')[:40]}... ({len(rows)} edges)")

    print("\n" + "="*40)
    print(f"Done! Saved to: {output_path}")
    print(f"Total Workflows Processed: {len(published_wfs)}")
    print(f"Total Connections Extracted: {total_connections}")
    if errors:
        print(f"Total Errors: {len(errors)}")

if __name__ == "__main__":
    main()