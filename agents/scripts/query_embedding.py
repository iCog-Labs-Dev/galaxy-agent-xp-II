#!/usr/bin/env python3
"""
Query Embedding Service

Generates embeddings for user queries using BAAI/bge-base-en-v1.5.
Importable and callable from other modules.
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
        print(f" Loaded embedding model: {model_name}")

    def embed_query(self, query: Union[str, List[str]]) -> np.ndarray:
        """
        Generate normalized embeddings for a single query or list of queries.
        """
        return self.model.encode(
            query,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False
        )


# ------------------ Singleton Instance ------------------ #
_embedding_service: QueryEmbeddingService | None = None


def get_query_embedding(query: Union[str, List[str]]) -> np.ndarray:
    """
    Generate embedding vector(s) for a query or list of queries.

    Args:
        query (str | List[str]): Query text(s)

    Returns:
        np.ndarray: Normalized embedding vector(s)
    """
    global _embedding_service

    if _embedding_service is None:
        _embedding_service = QueryEmbeddingService()

    return _embedding_service.embed_query(query)
