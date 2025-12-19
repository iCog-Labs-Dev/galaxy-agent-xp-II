#!/usr/bin/env python3
"""
Generate embeddings for Galaxy Tool metadata in a production-ready way.

Steps:
1. Load JSON metadata.
2. Build descriptive text per Tool for embeddings.
3. Encode texts using a SentenceTransformer model.
4. Save embeddings along with metadata (for Neo4j ingestion).
"""

import argparse
import json
import os
import time
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer


def build_tool_texts(tools: list[dict]) -> list[str]:
    """
    Convert each Tool record into a single text string for embedding.
    """
    texts = []
    for tool in tools:
        tool_id = tool.get("id") or ""
        name = tool.get("name") or ""
        description = tool.get("description") or ""
        version = tool.get("version") or ""
        help_text = tool.get("help") or ""
        categories = tool.get("categories") or []
        categories_str = ", ".join([c for c in categories if c])

        text = f"{tool_id} - {name} - {description} - {categories_str} - {version} - {help_text}"
        texts.append(text)
    return texts


def encode_tools(tools: list[dict], model_name: str) -> list[np.ndarray]:
    """
    Encode the list of tool texts into embeddings using a SentenceTransformer model.
    """
    print(f"🔄 Loading model: {model_name}")
    model = SentenceTransformer(model_name)

    texts = build_tool_texts(tools)
    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        show_progress_bar=True,
        normalize_embeddings=True  # normalize for cosine similarity
    )
    return embeddings


def save_embeddings(tools: list[dict], embeddings: np.ndarray, output_dir: str) -> None:
    """
    Save embeddings and metadata to the output directory with a timestamp.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")

    # Save embeddings as NumPy file
    emb_path = Path(output_dir) / f"tool_embeddings_{timestamp}.npy"
    np.save(emb_path, embeddings)

    # Merge embeddings into metadata and save as JSON
    tools_with_emb = [
        {**tool, "embedding": emb.tolist()} for tool, emb in zip(tools, embeddings)
    ]
    meta_path = Path(output_dir) / f"tool_metadata_with_embeddings_{timestamp}.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(tools_with_emb, f, ensure_ascii=False, indent=2)

    print(f"✅ Saved {len(embeddings)} embeddings to {emb_path}")
    print(f"✅ Saved metadata + embeddings to {meta_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate Tool embeddings for Neo4j ingestion.")
    parser.add_argument("--input", type=str, required=True, help="Path to JSON file with tool metadata.")
    parser.add_argument("--output-dir", type=str, default="embeddings", help="Directory to save embeddings and metadata.")
    parser.add_argument("--model", type=str, default="BAAI/bge-base-en-v1.5", help="Embedding model to use.")
    args = parser.parse_args()
    
    # Load input JSON
    with open(args.input, "r", encoding="utf-8") as f:
        tools = json.load(f)

    # Encode embeddings
    embeddings = encode_tools(tools, args.model)

    # Save embeddings and combined metadata
    save_embeddings(tools, embeddings, args.output_dir)


if __name__ == "__main__":
    main()
