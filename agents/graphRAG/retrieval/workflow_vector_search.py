import numpy as np
import logging
from agents.ingestion.Load.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)
logging.getLogger("neo4j").setLevel(logging.WARNING)


class WorkflowVectorSearch:
    """Vector search for Workflow nodes using Neo4j vector indexes for graph context."""

    def __init__(self, neo_client: Neo4jClient, index_name="workflow_embedding_index"):
        self.neo = neo_client
        self.index_name = index_name

    def search_top_k(self, query_embedding: np.ndarray, top_k: int = 5):
        if not isinstance(query_embedding, np.ndarray):
            raise ValueError("Query embedding must be a numpy ndarray")
        if query_embedding.ndim != 1:
            raise ValueError("Query embedding must be 1-dimensional")

        cypher = """
        CALL db.index.vector.queryNodes(
            $index_name,
            $top_k,
            $vector
        )
        YIELD node, score
        RETURN node.workflow_id AS workflow_id, score
        ORDER BY score DESC
        """

        try:
            result = self.neo.run_query(
                cypher,
                parameters={
                    "index_name": self.index_name,
                    "top_k": int(top_k),
                    "vector": query_embedding.astype(float).tolist(),
                }
            )
            return [(r["workflow_id"], r["score"]) for r in result]
        except Exception:
            logger.exception("Workflow vector search failed")
            return []