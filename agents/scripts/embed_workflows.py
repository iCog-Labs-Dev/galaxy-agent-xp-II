
"""
Generate embeddings for Galaxy / IWC Workflow metadata.

Steps:
1. Load cleaned workflow JSON.
2. Build semantic text per workflow.
3. Encode using BAAI/bge-base-en-v1.5.
4. Save embeddings + metadata (Neo4j-ready).
"""

import argparse
import json
import time
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer


def build_workflow_texts(workflows: list[dict]) -> list[str]:
    """
    Convert each workflow record into a single semantic text string for embedding.
    Works with both simplified (cleaned) and raw (full) workflow data.
    """
    texts = []
    for wf in workflows:
        repo = wf.get("workflow_repository") or ""
        category = wf.get("category") or ""
        
        # Try different readme field names (raw vs cleaned data)
        readme = wf.get("readme_content") or wf.get("readme_cleaned") or wf.get("readme") or ""
        
        # Extract tools from tool_names (simplified) or from steps (raw data)
        tools = wf.get("tool_names") or []
        if not tools and wf.get("workflow_files"):
            # Extract unique tool_ids from steps in raw data
            tool_ids = set()
            for wf_file in wf.get("workflow_files", []):
                for step in wf_file.get("steps", []):
                    tool_id = step.get("tool_id")
                    if tool_id:
                        tool_ids.add(tool_id)
            tools = list(tool_ids)

        tools_str = ", ".join(tools[:50])  # Limit to avoid very long strings

        text = (
            f"Workflow repository: {repo}. "
            f"Category: {category}. "
            f"Description: {readme[:1000]}. "  # Limit readme length
            f"Tools used: {tools_str}."
        )
        texts.append(text)

    return texts


def encode_workflows(workflows: list[dict], model_name: str) -> np.ndarray:
    """
    Encode workflow texts into normalized embeddings.
    """
    print(f"🔄 Loading model: {model_name}")
    model = SentenceTransformer(model_name)

    texts = build_workflow_texts(workflows)

    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        show_progress_bar=True,
        normalize_embeddings=True  
    )
    return embeddings


def save_embeddings(
    workflows: list[dict],
    embeddings: np.ndarray,
    output_dir: str,
    keep_all_fields: bool = True
) -> None:
    """
    Save embeddings and workflow metadata together.
    
    Args:
        workflows: List of workflow dictionaries
        embeddings: Numpy array of embeddings
        output_dir: Directory to save output files
        keep_all_fields: If True, keep all fields from input + add embedding.
                        If False, only keep selected fields (backward compatible).
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")

    # Save raw embeddings
    emb_path = Path(output_dir) / f"workflow_embeddings_{timestamp}.npy"
    np.save(emb_path, embeddings)

    if keep_all_fields:
        # Keep ALL fields from raw workflow data + add embedding
        workflows_with_emb = []
        for wf, emb in zip(workflows, embeddings):
            wf_copy = wf.copy()  # Keep all original fields
            wf_copy["embedding"] = emb.tolist()  # Add embedding
            workflows_with_emb.append(wf_copy)
    else:
        # Backward compatible: only keep selected fields (for cleaned/simplified data)
        workflows_with_emb = [
            {
                "workflow_repository": wf.get("workflow_repository"),
                "category": wf.get("category"),
                "tool_names": wf.get("tool_names"),
                "readme_cleaned": wf.get("readme_cleaned"),
                "raw_download_url": wf.get("raw_download_url"),
                "embedding": emb.tolist()
            }
            for wf, emb in zip(workflows, embeddings)
        ]

    meta_path = Path(output_dir) / f"workflow_metadata_with_embeddings_{timestamp}.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(workflows_with_emb, f, ensure_ascii=False, indent=2)

    print(f"✅ Encoded {len(embeddings)} workflows")
    print(f"💾 Embeddings saved to: {emb_path}")
    print(f"💾 Metadata + embeddings saved to: {meta_path}")
    if keep_all_fields:
        print(f"📦 Kept all fields from input data (workflow_files, steps, etc.)")


def main():
    parser = argparse.ArgumentParser(
        description="Generate workflow embeddings for Neo4j ingestion."
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to cleaned workflow metadata JSON file."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="embeddings",
        help="Directory to save embeddings and metadata."
    )
    parser.add_argument(
        "--model",
        type=str,
        default="BAAI/bge-base-en-v1.5",
        help="SentenceTransformer model to use."
    )
    parser.add_argument(
        "--keep-all-fields",
        action="store_true",
        default=True,
        help="Keep all fields from input data (workflow_files, steps, etc.) and add embedding. Default: True"
    )
    parser.add_argument(
        "--no-keep-all-fields",
        dest="keep_all_fields",
        action="store_false",
        help="Only keep selected fields (backward compatible mode)"
    )

    args = parser.parse_args()

    # Load workflows
    print(f"📥 Loading workflows from: {args.input}")
    with open(args.input, "r", encoding="utf-8") as f:
        workflows = json.load(f)
    
    print(f"📊 Loaded {len(workflows)} workflows")

    # Encode embeddings
    embeddings = encode_workflows(workflows, args.model)

    # Save results
    save_embeddings(workflows, embeddings, args.output_dir, keep_all_fields=args.keep_all_fields)


if __name__ == "__main__":
    main()
