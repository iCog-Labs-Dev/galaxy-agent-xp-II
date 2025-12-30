# agents/tool_suggestion_agent_pipeline.py
from typing import List, Dict
from pipeline.tool_retrieval_pipeline import ToolRetrievalPipeline
from agents.ingestion.Load.neo4j_client import Neo4jClient
from generation.tool_response_formater import format_tool_results

class ToolSuggestionAgent:
    """
    Wraps ToolRetrievalPipeline and exposes a suggest_tools method
    compatible with Pydantic response models.
    """

    def __init__(self, neo_client: Neo4jClient, top_k_default: int = 5):
        self.pipeline = ToolRetrievalPipeline(neo_client)
        self.top_k_default = top_k_default

    def suggest_tools(self, query: str, top_k: int = None) -> List[Dict]:
        top_k = top_k or self.top_k_default
        # Run the pipeline
        tools_ctx = self.pipeline.retrieve_tools(query, top_k=top_k)
        # Format results to match ToolSuggestion model
        formatted = format_tool_results(tools_ctx, query)
        return formatted["results"]