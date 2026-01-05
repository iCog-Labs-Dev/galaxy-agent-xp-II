import logging
from typing import Any, Dict, List, Sequence, Tuple

import numpy as np

logger = logging.getLogger(__name__)
logging.getLogger("neo4j").setLevel(logging.WARNING)


class ToolVectorSearch:
    """Vector search for Tool nodes with index-first then cosine fallback.

    The logic mirrors the embedding and search approach in agents/generic_loader:
    - embeddings stored on `Tool.embedding` are assumed normalized (see embed_nodes.py)
    - cosine similarity is computed via dot product if the vector index is unavailable
    """

    def __init__(
        self,
        neo_client: Any,
        index_name: str = "tool_embedding_index",
        label: str = "Tool",
        id_property: str = "tool_id",
    ) -> None:
        self.neo = neo_client
        self.index_name = index_name
        self.label = label
        self.id_property = id_property

    def search_top_k(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        allow_fallback: bool = True,
    ) -> List[Tuple[Any, float]]:
        """Return top-k `(tool_id, score)` tuples for the query embedding.

        The method tries the Neo4j native vector index first. If that fails
        (index missing or Neo4j version without vector support) and
        ``allow_fallback`` is True, it falls back to cosine similarity over
        stored embeddings, matching the computation in generic_loader/search.py.
        """

        q_vec = self._validate_and_normalize(query_embedding)

        index_hits = self._query_vector_index(q_vec, top_k)
        if index_hits:
            return index_hits

        if not allow_fallback:
            return []

        logger.info("Vector index search unavailable; using cosine fallback for Tool")
        return self._fallback_cosine_search(q_vec, top_k)

    def _validate_and_normalize(self, query_embedding: np.ndarray) -> np.ndarray:
        if not isinstance(query_embedding, np.ndarray):
            raise ValueError("Query embedding must be a numpy ndarray")
        if query_embedding.ndim != 1:
            raise ValueError("Query embedding must be 1-dimensional")
        q_vec = query_embedding.astype(np.float32).ravel()
        norm = float(np.linalg.norm(q_vec))
        if norm == 0.0:
            raise ValueError("Query embedding has zero norm")
        return q_vec / norm

    def _query_vector_index(self, q_vec: np.ndarray, top_k: int) -> List[Tuple[Any, float]]:
        cypher = """
        CALL db.index.vector.queryNodes(
            $index_name,
            $top_k,
            $vector
        )
        YIELD node, score
        RETURN node.tool_id AS tool_id, score
        ORDER BY score DESC
        """

        try:
            records = self._run_query(
                cypher,
                parameters={
                    "index_name": self.index_name,
                    "top_k": int(top_k),
                    "vector": q_vec.tolist(),
                },
            )
            return [(r["tool_id"], float(r["score"])) for r in records if r.get("tool_id") is not None]
        except Exception:
            logger.exception("Tool vector search via index failed")
            return []

    def _fallback_cosine_search(self, q_vec: np.ndarray, top_k: int) -> List[Tuple[Any, float]]:
        cypher = f"""
        MATCH (t:{self.label})
        WHERE t.embedding IS NOT NULL
        RETURN t.{self.id_property} AS tool_id, t.embedding AS embedding
        """

        try:
            records = self._run_query(cypher)
        except Exception:
            logger.exception("Tool cosine fallback query failed")
            return []

        embeddings: List[np.ndarray] = []
        ids: List[Any] = []
        for r in records:
            tool_id = r.get("tool_id") if isinstance(r, Dict) else r["tool_id"]
            emb = r.get("embedding") if isinstance(r, Dict) else r["embedding"]
            if tool_id is None or emb is None:
                continue
            vec = np.asarray(emb, dtype=np.float32).ravel()
            if vec.size == 0:
                continue
            embeddings.append(vec)
            ids.append(tool_id)

        if not embeddings:
            return []

        mat = np.vstack(embeddings)
        norms = np.linalg.norm(mat, axis=1, keepdims=True)
        mat = mat / np.maximum(norms, 1e-12)

        scores = mat @ q_vec
        top_idx = np.argsort(-scores)[: int(top_k)]
        return [(ids[i], float(scores[i])) for i in top_idx]

    def _run_query(self, cypher: str, parameters: Dict[str, Any] | None = None) -> Sequence[Dict[str, Any]]:
        """Run a Cypher query using the available Neo4j client interface."""

        if hasattr(self.neo, "run_query"):
            return self.neo.run_query(cypher, parameters=parameters or {})  # type: ignore[attr-defined]

        if hasattr(self.neo, "driver"):
            with self.neo.driver.session() as session:  # type: ignore[attr-defined]
                result = session.run(cypher, **(parameters or {}))
                return [dict(rec) for rec in result]

        raise AttributeError("Neo4j client does not expose run_query or driver")