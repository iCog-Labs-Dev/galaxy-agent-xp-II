#!/usr/bin/env python3
"""
Generate text embeddings for Galaxy workflow/tool metadata.

Steps:
1. Read a JSON file that matches the Galaxy metadata schema.
2. Convert each record into a single text string for embedding.
3. Encode those strings using a SentenceTransformer model.
4. Save both the embeddings and the original metadata with a timestamp.
"""

import argparse
import json
import os
import time
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer


def build_texts(data: list[dict]) -> list[str]:
    """
    Convert each metadata record into a single descriptive text string.

    - Joins category values into a comma-separated string.
    - Replaces nulls with an empty string.
    """
    texts = []
    for entry in data:
        categories = entry.get("categories") or []
        categories_str = ", ".join([c for c in categories if c])

        help_text = entry.get("help") or ""

        text = (
            f"{entry['id']} - {entry['name']} - {entry['description']} - "
            f"{categories_str} - {entry['version']} - {help_text}"
        )
        texts.append(text)
    return texts


def main(args: argparse.Namespace) -> None:
    # Load JSON metadata
    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Prepare text for embedding
    texts = build_texts(data)

    # Load the sentence-transformer model
    print(f"🔄 Loading model: {args.model}")
    model = SentenceTransformer(args.model)

    # Encode texts into embeddings
    embeddings = model.encode(
        texts,
        show_progress_bar=True,
        convert_to_numpy=True
    )

    # Ensure output directory exists
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Timestamped filenames for versioning
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    emb_path = output_dir / f"galaxy_embeddings_{timestamp}.npy"
    meta_path = output_dir / f"galaxy_metadata_{timestamp}.json"

    # Save embeddings and original metadata
    np.save(emb_path, embeddings)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Encoded {len(embeddings)} texts")
    print(f"💾 Embeddings saved to: {emb_path}")
    print(f"💾 Metadata saved to:  {meta_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate embeddings for Galaxy metadata."
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to the preprocessed JSON input file."
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
        default="intfloat/e5-base-v2",
        help="SentenceTransformer model to use."
    )

    main(parser.parse_args())
