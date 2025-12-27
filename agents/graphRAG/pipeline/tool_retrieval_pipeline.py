import logging
from typing import List, Dict, Optional
from agents.graphRAG.retrieval.tool_vector_search import ToolVectorSearch
from agents.graphRAG.retrieval.tool_graph_context import ToolGraphContext
from agents.scripts.query_embedding import QueryEmbeddingService
from agents.ingestion.Load.neo4j_client import Neo4jClient
from functools import lru_cache

logger = logging.getLogger(__name__)

class ToolRetrievalPipeline:
    """
    Production-ready tool retrieval pipeline:
    User Query → Vector Search → Top-K Tool IDs → Graph Traversal → Structured Context
    """

    def __init__(
        self,
        neo_client: Neo4jClient,
        embedding_service: Optional[QueryEmbeddingService] = None,
        cache_size: int = 128
    ):
        self.neo = neo_client
        self.embedder = QueryEmbeddingService()
        self.vector_search = ToolVectorSearch(neo_client)
        self.graph_context = ToolGraphContext(neo_client)

   
        self._cached_retrieve = lru_cache(maxsize=cache_size)(self._retrieve)

    def retrieve_tools(
        self, user_query: str, top_k: int = 5, use_cache: bool = True
    ) -> List[Dict]:
        """
        Retrieve structured tool context for a user query.

        Args:
            user_query (str): Query describing desired tool
            top_k (int): Number of top tools to retrieve
            use_cache (bool): Whether to use cached results

        Returns:
            List of structured tool contexts (dicts)
        """
        if not user_query:
            logger.warning("Empty user query provided to retrieve_tools")
            return []

        try:
            if use_cache:
                return self._cached_retrieve(user_query, top_k)
            else:
                return self._retrieve(user_query, top_k)
        except Exception as e:
            logger.error(f"Tool retrieval failed: {e}")
            return []

    def _retrieve(self, user_query: str, top_k: int) -> List[Dict]:
       
        query_vec = self.embedder.embed_query(user_query)

        top_tools = self.vector_search.search_top_k(query_vec, top_k)
        if not top_tools:
            logger.info(f"No tools found for query: '{user_query}'")
            return []

        tool_ids = [t[0] for t in top_tools]


        structured_context = self.graph_context.get_tool_context(tool_ids)


        score_map = {t[0]: t[1] for t in top_tools}
        for ctx in structured_context:
            tool_id = ctx.get("tool", {}).get("tool_id")
            ctx["similarity_score"] = score_map.get(tool_id, 0.0)

        return structured_context