import argparse
import csv
import json
from pathlib import Path
from typing import List, Dict, Any


def load_json(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        data = [data]
    return data


def write_csv(rows: List[Dict[str, Any]], path: Path) -> None:
    if not rows:
        print(f"⚠️ No rows to write for {path.name}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=fieldnames,
            quoting=csv.QUOTE_ALL,
            escapechar="\\",
            lineterminator="\n",
        )
        w.writeheader()
        w.writerows(rows)
    print(f"✅ Wrote {len(rows)} rows to {path}")


def convert_tools(tools: List[Dict[str, Any]], out_dir: Path):
    # Master tool rows
    tools_master = []
    # Category mappings (one row per category per tool)
    tool_categories = []
    # Inputs/Outputs
    tool_inputs = []
    tool_outputs = []

    for t in tools:
        tid = t.get("id") or ""
        name = t.get("name") or ""
        desc = t.get("description") or ""
        ver = t.get("version") or ""
        help_text = t.get("help") or ""
        cats = t.get("categories") or []
        if not cats:
            cats = ["unspecified"]

        tools_master.append({
            "id": tid,
            "name": name,
            "description": desc,
            "version": ver,
            "help": help_text,
        })

        for c in cats:
            tool_categories.append({
                "id": tid,
                "category": c,
            })

        for inp in (t.get("inputs") or []):
            tool_inputs.append({
                "id": tid,
                "input_name": inp.get("name") or "",
                "input_type": inp.get("type") or "",
            })

        for outp in (t.get("outputs") or []):
            tool_outputs.append({
                "id": tid,
                "output_name": outp.get("name") or "",
                "output_format": outp.get("format") if outp.get("format") is not None else "",
            })

    write_csv(tools_master, out_dir / "tools_master.csv")
    write_csv(tool_categories, out_dir / "tool_categories.csv")
    write_csv(tool_inputs, out_dir / "tool_inputs.csv")
    write_csv(tool_outputs, out_dir / "tool_outputs.csv")


def main():
    ap = argparse.ArgumentParser(description="Convert tools JSON to CSVs for generic loader")
    ap.add_argument("input_json", help="Path to tools JSON (from tools_metadata_downloader)")
    ap.add_argument("--output-dir", default=str(Path(__file__).parent / "data"), help="Directory for CSV outputs")
    args = ap.parse_args()

    input_path = Path(args.input_json)
    out_dir = Path(args.output_dir)
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    tools = load_json(input_path)
    convert_tools(tools, out_dir)


if __name__ == "__main__":
    main()
