# agents/workflow_vector_search/vector_search.py
import numpy as np
import logging
from agents.ingestion.Load.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)

class WorkflowVectorSearch:
    """
    Production-ready vector search for Workflow nodes in Neo4j.
    Uses GDS cosine similarity to retrieve top-K workflow IDs.
    """

    def __init__(self, neo_client: Neo4jClient):
        self.neo = neo_client

    def search_top_k(self, query_embedding: np.ndarray, top_k: int = 5):
        """
        Perform KNN vector search using Neo4j GDS.
        Returns top-K workflow IDs with similarity scores.

        Args:
            query_embedding (np.ndarray): Normalized query vector
            top_k (int): Number of top results to return

        Returns:
            List of tuples: [(workflow_id, similarity_score), ...]
        """
        if query_embedding is None or not isinstance(query_embedding, np.ndarray):
            logger.error("Invalid query embedding provided")
            return []

        cypher = """
        CALL gds.alpha.similarity.cosine.stream({
            nodeProjection: 'Workflow',
            vectorProperty: 'embedding',
            topK: $top_k,
            queryVector: $query_vector
        })
        YIELD nodeId, similarity
        RETURN gds.util.asNode(nodeId).workflow_id AS workflow_id, similarity
        ORDER BY similarity DESC
        """

        try:
            result = self.neo.run_query(
                cypher,
                params={"query_vector": query_embedding.tolist(), "top_k": top_k}
            )
            return [(r["workflow_id"], r["similarity"]) for r in result]

        except Exception as e:
            logger.error(f"Workflow vector search failed: {e}")
            return []
