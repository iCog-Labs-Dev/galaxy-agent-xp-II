import argparse
import csv
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Iterable, Type

from convertor_schema import (
    InputConnectionProperties,
    InputProperties,
    OutputProperties,
    StepsInWorkflowFileProperties,
    StepSequenceRow,
    ToolsInStepsProperties,
    ToolsInWorkflowFileProperties,
    WorkflowFileProperties,
    WorkflowProperties,
)


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
        schema_validated_tools = ToolsInStepsProperties(
            id=str(tool_id),
            name=step.get("name") or "",
            version=step.get("tool_version") or "",
            owner=repo.get("owner", ""),
            category=repo.get("category", ""),
            tool_shed_url=repo.get("tool_shed", ""),
        )

        tools.append(schema_validated_tools.model_dump())
    return tools


def _validated_dict(model: Type, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Validate payload with pydantic model and return its dict."""
    return model(**payload).model_dump()


def _slugify_repository_name(value: str) -> str:
    normalized = re.sub(r"\s+", "_", (value or "").strip().lower())
    normalized = re.sub(r"[^a-z0-9_\-]+", "_", normalized)
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized


def to_workflows_csv_rows(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]: # TODO: Fix worklfow updloading schema!!
    rows = []
    seen: set[tuple[str, str]] = set()

    def add_workflow_row(category: str, workflow_repository: str, workflow_name: str, readme_content: str):
        key = (category, workflow_repository)
        if not workflow_repository or key in seen:
            return
        seen.add(key)
        rows.append(
            _validated_dict(
                WorkflowProperties,
                {
                    "category": category,
                    "workflow_repository": workflow_repository,
                    "workflow_name": workflow_name,
                    "readme_content": readme_content,
                },
            )
        )

    for wf in data:
        category = wf.get("category", "")
        parent_repo = wf.get("workflow_repository", "")
        readme_content = wf.get("readme_content",  wf.get("description",  wf.get("annotation", ""))) or ""
        parent_name = parent_repo

        workflow_files = wf.get("workflow_files", []) or []
        if workflow_files:
            parent_name = (workflow_files[0].get("workflow_name") or parent_repo).strip() or parent_repo

        add_workflow_row(category, parent_repo, parent_name, readme_content)

        for wf_file in workflow_files:
            wf_name = (wf_file.get("workflow_name") or "").strip()
            if not wf_name:
                continue
            standalone_repo = _slugify_repository_name(wf_name)
            add_workflow_row(category, standalone_repo, wf_name, readme_content)

    return rows


def to_workflow_files_csv_rows(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for wf in data:
        for wf_file in wf.get("workflow_files", []) or []:
            rows.append(
                _validated_dict(
                    WorkflowFileProperties,
                    {
                        "category": wf.get("category", ""),
                        "workflow_repository": wf.get("workflow_repository", ""),
                        "workflow_name": wf_file.get("workflow_name", ""),
                        "number_of_steps": wf_file.get("number_of_steps", 0),
                        "file_name": wf_file.get("file_name", ""),
                        "raw_download_url": wf_file.get("raw_download_url", ""),
                        "tools_used_count": len(
                            wf_file.get("tools_used")
                            or derive_tools_from_steps(wf_file.get("steps", []))
                        ),
                    },
                )
            )
    return rows

def to_tools_used_csv_rows(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for wf in data:
        for wf_file in wf.get("workflow_files", []) or []:
            tools = wf_file.get("tools_used")
            if tools is None:
                tools = derive_tools_from_steps(wf_file.get("steps", []))
            for tool in tools or []:
                rows.append(
                    _validated_dict(
                        ToolsInWorkflowFileProperties,
                        {
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
                        },
                    )
                )
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
                annotation = step.get("annotation", "")
                sub_name = step.get("subworkflow_name", "")
                if step.get("type") == "subworkflow":
                    booster = f"Executes a composite subworkflow named {sub_name or 'a nested subworkflow'} to perform a multi-step wrapped process."
                    annotation = f"{annotation} | {booster}" if annotation else booster

                rows.append(
                    _validated_dict(
                        StepsInWorkflowFileProperties,
                        {
                            "category": wf.get("category", ""),
                            "workflow_repository": wf.get("workflow_repository", ""),
                            "workflow_name": wf_file.get("workflow_name", ""),
                            "file_name": wf_file.get("file_name", ""),
                            "step_id": step.get("step_id"),
                            "type": step.get("type", ""),
                            "name": step.get("name", ""),
                            "annotation": annotation,
                            "subworkflow_name": sub_name,
                            "tool_id": step.get("tool_id", ""),
                            "tool_version": step.get("tool_version", ""),
                            "inputs_count": len(step.get("inputs", []) or []),
                            "outputs_count": len(step.get("outputs", []) or []),
                        },
                    )
                )
    return rows


def _step_sort_key(step: Dict[str, Any]) -> Any:
    step_id = step.get("step_id")
    try:
        return int(step_id)
    except (TypeError, ValueError):
        return step_id or 0


def to_step_sequence_csv_rows(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for wf in data:
        for wf_file in wf.get("workflow_files", []) or []:
            steps = sorted(wf_file.get("steps", []) or [], key=_step_sort_key)
            if len(steps) < 2:
                continue

            for idx in range(len(steps) - 1):
                current = steps[idx]
                nxt = steps[idx + 1]
                rows.append(
                    _validated_dict(
                        StepSequenceRow,
                        {
                            "category": wf.get("category", ""),
                            "workflow_repository": wf.get("workflow_repository", ""),
                            "workflow_name": wf_file.get("workflow_name", ""),
                            "file_name": wf_file.get("file_name", ""),
                            "from_step_id": current.get("step_id"),
                            "to_step_id": nxt.get("step_id"),
                            "sequence_index": idx + 1,
                        },
                    )
                )

    return rows


def to_step_inputs_csv_rows(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for wf in data:
        for wf_file in wf.get("workflow_files", []) or []:
            for step in wf_file.get("steps", []) or []:
                for io in _flatten_ios(step.get("inputs", [])):
                    rows.append(
                        _validated_dict(
                            InputProperties,
                            {
                                "category": wf.get("category", ""),
                                "workflow_repository": wf.get("workflow_repository", ""),
                                "workflow_name": wf_file.get("workflow_name", ""),
                                "file_name": wf_file.get("file_name", ""),
                                "step_id": step.get("step_id"),
                                **io,
                            },
                        )
                    )
    return rows


def to_step_outputs_csv_rows(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for wf in data:
        for wf_file in wf.get("workflow_files", []) or []:
            for step in wf_file.get("steps", []) or []:
                for io in _flatten_ios(step.get("outputs", [])):
                    rows.append(
                        _validated_dict(
                            OutputProperties,
                            {
                                "category": wf.get("category", ""),
                                "workflow_repository": wf.get("workflow_repository", ""),
                                "workflow_name": wf_file.get("workflow_name", ""),
                                "file_name": wf_file.get("file_name", ""),
                                "step_id": step.get("step_id"),
                                **io,
                            },
                        )
                    )
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
                        rows.append(
                            _validated_dict(
                                InputConnectionProperties,
                                {
                                    "category": wf.get("category", ""),
                                    "workflow_repository": wf.get("workflow_repository", ""),
                                    "workflow_name": wf_file.get("workflow_name", ""),
                                    "file_name": wf_file.get("file_name", ""),
                                    "step_id": step.get("step_id"),
                                    "input_name": input_name,
                                    "from_step_id": c.get("id"),
                                    "from_output_name": c.get("output_name", ""),
                                },
                            )
                        )
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
    write_csv(to_step_sequence_csv_rows(data), output_dir / "step_sequences.csv")


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
