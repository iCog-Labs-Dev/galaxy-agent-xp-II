# agents/workflow_suggestion_agent.py
from typing import Any, Dict, List

from generation.workflow_response_formater import format_workflow_results
from pipeline.workflow_retrival_pipeline import WorkflowRetrievalPipeline

class WorkflowSuggestionAgent:
    """
    Wraps WorkflowRetrievalPipeline and exposes a suggest_workflows method
    compatible with Pydantic response models.
    """

    def __init__(self, neo_client: Any, top_k_default: int = 5):
        self.pipeline = WorkflowRetrievalPipeline(neo_client)
        self.top_k_default = top_k_default

    def suggest_workflows(self, query: str, top_k: int = None) -> List[Dict]:
        top_k = top_k or self.top_k_default
        # Run the pipeline
        workflows_ctx = self.pipeline.retrieve_workflows(query, top_k=top_k)
        # Format results to match WorkflowSuggestionResponse model
        formatted = format_workflow_results(workflows_ctx, query)
        return formatted["results"]