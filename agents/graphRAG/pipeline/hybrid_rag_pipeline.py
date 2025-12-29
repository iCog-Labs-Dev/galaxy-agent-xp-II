# agents/pipeline/hybrid_rag_pipeline.py
import logging
from typing import List, Dict, Optional
from agents.graphRAG.generation.answer_generator import LLMAnswerGenerator
from agents.classification_service import classify_query
from agents.graphRAG.pipeline.workflow_retrival_pipeline import WorkflowRetrievalPipeline
from agents.graphRAG.pipeline.tool_retrieval_pipeline import ToolRetrievalPipeline
from agents.ingestion.Load.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)

from agents.summary_agent import summarize_tool_suggestions, summarize_workflow_suggestions
from agents.graphRAG.generation.answer_generator import LLMAnswerGenerator

class HybridRAGPipeline:
    def __init__(self, neo_client):
        self.tool_pipeline = ToolRetrievalPipeline(neo_client)
        self.workflow_pipeline = WorkflowRetrievalPipeline(neo_client)
        self.answer_gen = LLMAnswerGenerator()

    def run(self, query: str, top_k: int = 5) -> dict:
        classification = classify_query(query)
        intent = classification.get("label", "both") if isinstance(classification, dict) else "both"
        tool_ctx, workflow_ctx = [], []

        if intent in ["tool", "both"]:
            tool_ctx = self.tool_pipeline.retrieve_tools(query, top_k)
        if intent in ["workflow", "both"]:
            workflow_ctx = self.workflow_pipeline.retrieve_workflows(query, top_k)

        # Generate results using deterministic formatter
        results = self.answer_gen.generate(
            query=query,
            intent=intent,
            tools=tool_ctx,
            workflows=workflow_ctx
        )

        # summaries
        tool_summary = summarize_tool_suggestions(tool_ctx, query) if tool_ctx else None
        workflow_summary = summarize_workflow_suggestions(workflow_ctx, query) if workflow_ctx else None

        # results + summaries
        return {
            "results": results.get("results", []),
            "tool_summary": tool_summary,
            "workflow_summary": workflow_summary
        }