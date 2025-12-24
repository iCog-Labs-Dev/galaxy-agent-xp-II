# agents/workflow_suggestion_agent.py
from typing import List, Dict
from agents.graphRAG.pipeline.workflow_retrival_pipeline import WorkflowRetrievalPipeline
from agents.ingestion.Load.neo4j_client import Neo4jClient
from agents.graphRAG.generation.workflow_response_formater import format_workflow_results

class WorkflowSuggestionAgent:
    """
    Wraps WorkflowRetrievalPipeline and exposes a suggest_workflows method
    compatible with Pydantic response models.
    """

    def __init__(self, neo_client: Neo4jClient, top_k_default: int = 5):
        self.pipeline = WorkflowRetrievalPipeline(neo_client)
        self.top_k_default = top_k_default

    def suggest_workflows(self, query: str, top_k: int = None) -> List[Dict]:
        top_k = top_k or self.top_k_default
        # Run the pipeline
        workflows_ctx = self.pipeline.retrieve_workflows(query, top_k=top_k)
        # Format results to match WorkflowSuggestionResponse model
        formatted = format_workflow_results(workflows_ctx, query)
        return formatted["results"]
