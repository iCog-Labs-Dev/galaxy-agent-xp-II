import numpy as np
import logging
from agents.ingestion.Load.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)
logging.getLogger("neo4j").setLevel(logging.WARNING)

class ToolVectorSearch:
    """
    Production-ready vector search for Tool nodes in Neo4j 5.x+
    """

    def __init__(self, neo_client: Neo4jClient, index_name="tool_embedding_index"):
        self.neo = neo_client
        self.index_name = index_name

    def search_top_k(self, query_embedding: np.ndarray, top_k: int = 5):
        """
        Perform vector search on Tool nodes.

        Returns:
            List[(tool_id, score)]
        """
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
        RETURN node.tool_id AS tool_id, score
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

            return [(r["tool_id"], r["score"]) for r in result]

        except Exception:
            logger.exception("Tool vector search failed")
            return []