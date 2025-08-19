import argparse
import json
import os
import time
import numpy as np
from sentence_transformers import SentenceTransformer


def main(args):
    # Load data
    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Structure text data
    texts = [
        f"{entry['name']} - {entry['description']} - {entry['categories']} - {entry['help']}"
        for entry in data
    ]

    # Load model
    print(f"Loading model: {args.model}")
    model = SentenceTransformer(args.model)

    # Encode texts
    embeddings = model.encode(
        texts,
        show_progress_bar=True,
        convert_to_numpy=True
    )

    # Ensure output dir exists
    os.makedirs(args.output_dir, exist_ok=True)

    # Timestamp for versioning
    timestamp = time.strftime("%Y%m%d_%H%M%S")

    # Save embeddings
    emb_path = os.path.join(args.output_dir, f"galaxy_embeddings_{timestamp}.npy")
    meta_path = os.path.join(args.output_dir, f"galaxy_metadata_{timestamp}.json")

    np.save(emb_path, embeddings)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Encoded {len(embeddings)} texts")
    print(f"💾 Embeddings saved to: {emb_path}")
    print(f"💾 Metadata saved to: {meta_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate embeddings for Galaxy metadata.")

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

    args = parser.parse_args()
    main(args)
