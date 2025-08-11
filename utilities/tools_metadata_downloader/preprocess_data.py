import json
import re
import os
from datetime import datetime
from pathlib import Path

def clean_help_text(text):
    # Remove HTML/XML-like tags (e.g., <help>)
    text = re.sub(r"<[^>]+>", " ", text)
    # Replace multiple underscores and equals signs used for formatting
    text = re.sub(r"[=_]{2,}", " ", text)
    # Remove ASCII box drawing characters (used in tables)
    text = re.sub(r"[│║╔╗╚╝╠╣═╦╩╬┼─┐└┘┌┴┬├┤┬┴┼]", " ", text)
    # Remove +—-table borders and markdown-like table lines
    text = re.sub(r"[\+\|\-]+", " ", text)
    # Remove newline characters and extra whitespace
    text = re.sub(r"\s+", " ", text).strip()
    # Remove specific markdown formatting characters
    text = re.sub(r"[\*_`]", "", text) 
    return text

def preprocess_file(input_path, output_dir="utilities/tools_metadata_downloader/data"):
    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for tool in data:
        if "help" in tool and isinstance(tool["help"], str):
            tool["help"] = clean_help_text(tool["help"])

    # Generate timestamped output filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"preprocessed_tools_{timestamp}.json"
    output_path = os.path.join(output_dir, output_filename)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✅ Preprocessed help fields saved to: {output_path}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Preprocess help sections in Galaxy tool metadata JSON.")
    parser.add_argument("input_file", type=str, help="Path to the downloaded JSON file.")
    args = parser.parse_args()

    preprocess_file(args.input_file)
