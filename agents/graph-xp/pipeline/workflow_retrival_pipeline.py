import logging
from functools import lru_cache
from typing import Any, Dict, List, Optional

from retrieval.workflow_vector_search import WorkflowVectorSearch
from retrieval.workflow_graph_context import WorkflowGraphContext
from scripts.query_embedding import QueryEmbeddingService

logger = logging.getLogger(__name__)


class WorkflowRetrievalPipeline:
    """
    Full workflow recommendation pipeline:
    User query → embedding → vector search → graph context → structured workflows-organized dicts
    """

    def __init__(
        self,
        neo_client: Any,
        embedding_service: Optional[QueryEmbeddingService] = None,
        cache_size: int = 128
    ):
        self.neo = neo_client
        self.embedder = embedding_service or QueryEmbeddingService()
        self.vector_search = WorkflowVectorSearch(neo_client)
        self.graph_context = WorkflowGraphContext(neo_client)
        self._cached_retrieve = lru_cache(maxsize=cache_size)(self._retrieve)

    def retrieve_workflows(self, user_query: str, top_k: int = 5, use_cache: bool = True) -> List[Dict]:
        if not user_query:
            logger.warning("Empty query provided to retrieve_workflows")
            return []

        try:
            if use_cache:
                return self._cached_retrieve(user_query, top_k)
            return self._retrieve(user_query, top_k)
        except Exception:
            logger.exception("Workflow retrieval failed")
            return []

    def _retrieve(self, user_query: str, top_k: int) -> List[Dict]:
        # Step 1: embed query
        query_vec = self.embedder.embed_query(user_query)

        # Step 2: vector search
        top_workflows = self.vector_search.search_top_k(query_vec, top_k)
        if not top_workflows:
            logger.info(f"No workflows found for query: '{user_query}'")
            return []

        workflow_ids = [wf[0] for wf in top_workflows]

        # Step 3: get graph context
        structured_context = self.graph_context.get_workflow_context(workflow_ids)

        # Step 4: attach similarity scores 
        score_map = {}
        for wf_id, score in top_workflows:
            try:
                score_map[wf_id] = float(score)
            except (TypeError, ValueError):
                logger.warning(f"Invalid score for workflow {wf_id}: {score}, defaulting to 0.0")
                score_map[wf_id] = 0.0

        for ctx in structured_context:
            wf_node = ctx.get("workflow", {})
            wf_id = wf_node.get("workflow_id")
            ctx["similarity_score"] = score_map.get(wf_id, 0.0)

        return structured_context