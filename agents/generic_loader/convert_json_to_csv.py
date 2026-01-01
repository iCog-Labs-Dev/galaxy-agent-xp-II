import argparse
import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Iterable


def load_json(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        data = [data]
    return data


def derive_tools_from_steps(steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    tools = []
    seen_ids = set()
    for step in steps or []:
        tool_id = step.get("tool_id")
        if not tool_id:
            continue
        if tool_id in seen_ids:
            continue
        seen_ids.add(tool_id)
        repo = step.get("tool_shed_repository") or {}
        tools.append({
            "id": str(tool_id),
            "name": step.get("name") or "",
            "version": step.get("tool_version") or "",
            "owner": repo.get("owner", ""),
            "category": repo.get("category", ""),
            "tool_shed_url": repo.get("tool_shed", ""),
        })
    return tools


def to_workflows_csv_rows(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for wf in data:
        rows.append({
            "category": wf.get("category", ""),
            "workflow_repository": wf.get("workflow_repository", ""),
            "has_readme": wf.get("has_readme", False),
            "has_dockstore_yml": wf.get("has_dockstore_yml", False),
            "has_test_data": wf.get("has_test_data", False),
            "has_changelog": wf.get("has_changelog", False),
            "planemo_tests": ";".join(wf.get("planemo_tests", [])),
            "readme_content": wf.get("readme_content", "") or "",
        })
    return rows


def to_workflow_files_csv_rows(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for wf in data:
        for wf_file in wf.get("workflow_files", []) or []:
            rows.append({
                "category": wf.get("category", ""),
                "workflow_repository": wf.get("workflow_repository", ""),
                "workflow_name": wf_file.get("workflow_name", ""),
                "number_of_steps": wf_file.get("number_of_steps", 0),
                "file_name": wf_file.get("file_name", ""),
                "raw_download_url": wf_file.get("raw_download_url", ""),
                "tools_used_count": len(wf_file.get("tools_used") or derive_tools_from_steps(wf_file.get("steps", []))),
            })
    return rows


def to_tools_used_csv_rows(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for wf in data:
        for wf_file in wf.get("workflow_files", []) or []:
            tools = wf_file.get("tools_used")
            if tools is None:
                tools = derive_tools_from_steps(wf_file.get("steps", []))
            for tool in tools or []:
                rows.append({
                    "category": wf.get("category", ""),
                    "workflow_repository": wf.get("workflow_repository", ""),
                    "workflow_name": wf_file.get("workflow_name", ""),
                    "file_name": wf_file.get("file_name", ""),
                    "id": tool.get("id", ""),
                    "name": tool.get("name", ""),
                    "version": tool.get("version", ""),
                    "owner": tool.get("owner", ""),
                    "tool_category": tool.get("category", ""),
                    "tool_shed_url": tool.get("tool_shed_url", ""),
                })
    return rows


def _flatten_ios(step_ios: Iterable[Dict[str, Any]]):
    for io in step_ios or []:
        yield {
            "name": io.get("name", ""),
            "type": io.get("type", ""),
            "description": io.get("description", ""),
            "optional": io.get("optional", False),
        }


def to_steps_csv_rows(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for wf in data:
        for wf_file in wf.get("workflow_files", []) or []:
            for step in wf_file.get("steps", []) or []:
                rows.append({
                    "category": wf.get("category", ""),
                    "workflow_repository": wf.get("workflow_repository", ""),
                    "workflow_name": wf_file.get("workflow_name", ""),
                    "file_name": wf_file.get("file_name", ""),
                    "step_id": step.get("step_id"),
                    "type": step.get("type", ""),
                    "name": step.get("name", ""),
                    "annotation": step.get("annotation", ""),
                    "tool_id": step.get("tool_id", ""),
                    "tool_version": step.get("tool_version", ""),
                    "inputs_count": len(step.get("inputs", []) or []),
                    "outputs_count": len(step.get("outputs", []) or []),
                })
    return rows


def to_step_inputs_csv_rows(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for wf in data:
        for wf_file in wf.get("workflow_files", []) or []:
            for step in wf_file.get("steps", []) or []:
                for io in _flatten_ios(step.get("inputs", [])):
                    rows.append({
                        "category": wf.get("category", ""),
                        "workflow_repository": wf.get("workflow_repository", ""),
                        "workflow_name": wf_file.get("workflow_name", ""),
                        "file_name": wf_file.get("file_name", ""),
                        "step_id": step.get("step_id"),
                        **io,
                    })
    return rows


def to_step_outputs_csv_rows(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for wf in data:
        for wf_file in wf.get("workflow_files", []) or []:
            for step in wf_file.get("steps", []) or []:
                for io in _flatten_ios(step.get("outputs", [])):
                    rows.append({
                        "category": wf.get("category", ""),
                        "workflow_repository": wf.get("workflow_repository", ""),
                        "workflow_name": wf_file.get("workflow_name", ""),
                        "file_name": wf_file.get("file_name", ""),
                        "step_id": step.get("step_id"),
                        **io,
                    })
    return rows


def to_input_connections_csv_rows(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for wf in data:
        for wf_file in wf.get("workflow_files", []) or []:
            for step in wf_file.get("steps", []) or []:
                conns = step.get("input_connections") or {}
                for input_name, conn in (conns.items() if isinstance(conns, dict) else []):
                    conn_list = conn if isinstance(conn, list) else [conn]
                    for c in conn_list:
                        rows.append({
                            "category": wf.get("category", ""),
                            "workflow_repository": wf.get("workflow_repository", ""),
                            "workflow_name": wf_file.get("workflow_name", ""),
                            "file_name": wf_file.get("file_name", ""),
                            "step_id": step.get("step_id"),
                            "input_name": input_name,
                            "from_step_id": c.get("id"),
                            "from_output_name": c.get("output_name", ""),
                        })
    return rows


def write_csv(rows: List[Dict[str, Any]], path: Path) -> None:
    if not rows:
        print(f"⚠️ No rows to write for {path.name}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
            quoting=csv.QUOTE_ALL,
            escapechar="\\",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"✅ Wrote {len(rows)} rows to {path}")


def convert(input_path: Path, output_dir: Path) -> None:
    data = load_json(input_path)
    write_csv(to_workflows_csv_rows(data), output_dir / "workflows.csv")
    write_csv(to_workflow_files_csv_rows(data), output_dir / "workflow_files.csv")
    write_csv(to_tools_used_csv_rows(data), output_dir / "tools_used.csv")
    write_csv(to_steps_csv_rows(data), output_dir / "workflow_steps.csv")
    write_csv(to_step_inputs_csv_rows(data), output_dir / "step_inputs.csv")
    write_csv(to_step_outputs_csv_rows(data), output_dir / "step_outputs.csv")
    write_csv(to_input_connections_csv_rows(data), output_dir / "step_input_connections.csv")


def main():
    parser = argparse.ArgumentParser(description="Convert IWC JSON to CSVs for generic loader")
    parser.add_argument("input_json", help="Path to iwc_downloader JSON (e.g., iwc_full_*.json)")
    parser.add_argument("--output-dir", default=str(Path(__file__).parent / "data"), help="Directory for CSV outputs")
    args = parser.parse_args()

    input_path = Path(args.input_json)
    output_dir = Path(args.output_dir)
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    convert(input_path, output_dir)


if __name__ == "__main__":
    main()
