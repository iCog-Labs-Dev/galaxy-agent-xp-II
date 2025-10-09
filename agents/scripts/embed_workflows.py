import argparse
import json
import os
import time
import numpy as np
from sentence_transformers import SentenceTransformer


def main(args):
    # Load workflow metadata
    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Structure texts for embedding
    texts = []
    metadata_for_saving = []   # Store metadata with download URLs for saving
    for entry in data:
        workflow_repo = entry.get("workflow_repository", "")
        category = entry.get("category", "")
        readme = entry.get("readme_cleaned", "")
        tools = entry.get("tool_names", [])
        raw_download_url = entry.get("raw_download_url", "") 
        

        # Build structured text embedding
        text = (
            f"Workflow Repository: {workflow_repo}. "
            f"Category: {category}. "
            f"Description: {readme}. "
            f"Tools Used: {', '.join(tools)}."
            f"Download URL: {raw_download_url}" 
        )
        texts.append(text)

            # Store complete metadata including download URL for saving
        metadata_for_saving.append({
            "workflow_repository": workflow_repo,
            "category": category,
            "tool_names": tools,
            "readme_cleaned": readme,
            "raw_download_url": raw_download_url})

    # Load model
    print(f"Loading model: {args.model}")
    model = SentenceTransformer(args.model)

    # Encode workflows
    embeddings = model.encode(
        texts,
        show_progress_bar=True,
        convert_to_numpy=True
    )

    # Ensure output dir exists
    os.makedirs(args.output_dir, exist_ok=True)

    # Timestamp for versioning
    timestamp = time.strftime("%Y%m%d_%H%M%S")

    # Save embeddings + metadata
    emb_path = os.path.join(args.output_dir, f"iwc_workflow_embeddings_{timestamp}.npy")
    meta_path = os.path.join(args.output_dir, f"iwc_workflow_metadata_{timestamp}.json")

    np.save(emb_path, embeddings)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Encoded {len(embeddings)} workflows")
    print(f"💾 Embeddings saved to: {emb_path}")
    print(f"💾 Metadata saved to: {meta_path}")
    print(f"📥 Download URLs included in both embedded text and metadata")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate embeddings for IWC workflows metadata.")

    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to the preprocessed IWC workflows JSON file."
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="agents/embeddings",
        help="Directory where embeddings and metadata will be saved."
    )

    parser.add_argument(
        "--model",
        type=str,
        default="johnnas12/e5-galaxy-finetuned",
        help="SentenceTransformer model to use."
    )

    args = parser.parse_args()
    main(args)
