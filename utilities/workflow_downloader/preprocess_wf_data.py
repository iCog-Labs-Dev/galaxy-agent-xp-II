import os
import re
import json
import argparse
from pathlib import Path
from datetime import datetime

def clean_readme(text):
    if not isinstance(text, str):
        return ""
    text = re.sub(r"<[^>]+>", " ", text)               # Remove HTML/XML tags
    text = re.sub(r"[=_]{2,}", " ", text)              # Formatting lines
    text = re.sub(r"[│║╔╗╚╝╠╣═╦╩╬┼─┐└┘┌┴┬├┤┬┴┼]", " ", text)
    text = re.sub(r"[\+\|\-]+", " ", text)             # Markdown table lines
    text = re.sub(r"\s+", " ", text)                   # Extra whitespace
    text = re.sub(r"[*_`#]", "", text)                 # Markdown characters
    return text.strip()

def preprocess_workflow_file(input_file, output_dir):
    with open(input_file, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)# ← Reads iwc_downloader's output
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in {input_file}: {e}")
            return

    # Ensure it is a list (list of workflows)
    if not isinstance(data, list):
        data = [data]

    preprocessed = []

    for workflow in data:
        # Extract tool names from all workflow_files > tools_used
        tool_names = []
        for wf_file in workflow.get("workflow_files", []):
            raw_download_url = wf_file.get("raw_download_url", "")
            for tool in wf_file.get("tools_used", []):
                name = tool.get("name")
                if name:
                    tool_names.append(name)

    # Clean README content
        cleaned_readme = clean_readme(workflow.get("readme_content", ""))

        # Create simplified structure
        preprocessed.append({
            "category": workflow.get("category", ""),
            "workflow_repository": workflow.get("workflow_repository", ""),
            "tool_names": tool_names, # ← Flattened tool list
            "readme_cleaned": cleaned_readme, 
            "raw_download_url": raw_download_url,
        })

    # Output with timestamp
      # Save preprocessed data: preprocessed_workflows_20250908_123041.json
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"preprocessed_workflows_{timestamp}.json"
    output_path = Path(output_dir) / output_filename
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(preprocessed, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Preprocess Galaxy workflow metadata.")
    parser.add_argument("input_path", help="Path to JSON file or directory of JSON files")
    parser.add_argument("--output_dir", default="utilities/workflow_downloader/data", help="Directory to save output")

    args = parser.parse_args()
    input_path = Path(args.input_path)

    if input_path.is_file() and input_path.suffix == ".json":
        preprocess_workflow_file(input_path, args.output_dir)
    elif input_path.is_dir():
        for file in input_path.glob("*.json"):
            preprocess_workflow_file(file, args.output_dir)
    else:
        print("❌ Invalid input. Provide a JSON file or a directory containing JSON files.")

if __name__ == "__main__":
    main()
