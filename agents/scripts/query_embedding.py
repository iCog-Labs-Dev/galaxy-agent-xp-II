#!/usr/bin/env python3
"""
Query Embedding Service

Generates embeddings for user queries using BAAI/bge-base-en-v1.5.
This service is importable and also testable from command line.
"""

from sentence_transformers import SentenceTransformer
import numpy as np
from typing import Union, List

# ------------------ Configuration ------------------ #
MODEL_NAME = "BAAI/bge-base-en-v1.5"

# ------------------ Query Embedding Class ------------------ #
class QueryEmbeddingService:
    def __init__(self, model_name: str = MODEL_NAME):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        print(f"🔄 Loaded embedding model: {model_name}")

    def embed_query(self, query: Union[str, List[str]]) -> np.ndarray:
        """
        Generate normalized embeddings for a single query or list of queries.

        Args:
            query (str | List[str]): Single query string or list of query strings.

        Returns:
            np.ndarray: Normalized embedding vector(s).
        """
        embeddings = self.model.encode(
            query,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False
        )
        return embeddings


# ------------------ CLI Test Interface ------------------ #
def main():
    service = QueryEmbeddingService()
    print("\n Query Embedding Test")
    print("Type 'exit' to quit.\n")

    while True:
        query = input("Enter a query: ").strip()
        if query.lower() == "exit":
            break
        if not query:
            print(" Please enter a non-empty query.\n")
            continue

        vector = service.embed_query(query)
        print(f"\nEmbedding vector shape: {vector.shape}")
        print("First 10 values:", vector[:10], "\n")


if __name__ == "__main__":
    main()
