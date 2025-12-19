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
    """
    texts = []
    for wf in workflows:
        repo = wf.get("workflow_repository") or ""
        category = wf.get("category") or ""
        readme = wf.get("readme_cleaned") or ""
        tools = wf.get("tool_names") or []

        tools_str = ", ".join(tools)

        text = (
            f"Workflow repository: {repo}. "
            f"Category: {category}. "
            f"Description: {readme}. "
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
    output_dir: str
) -> None:
    """
    Save embeddings and workflow metadata together.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")

    # Save raw embeddings
    emb_path = Path(output_dir) / f"workflow_embeddings_{timestamp}.npy"
    np.save(emb_path, embeddings)

    # Merge embeddings into metadata (Neo4j-ready)
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

    args = parser.parse_args()

    # Load workflows
    with open(args.input, "r", encoding="utf-8") as f:
        workflows = json.load(f)

    # Encode embeddings
    embeddings = encode_workflows(workflows, args.model)

    # Save results
    save_embeddings(workflows, embeddings, args.output_dir)


if __name__ == "__main__":
    main()
