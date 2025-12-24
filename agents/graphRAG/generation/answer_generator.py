import logging
from typing import List, Dict, Optional

from agents.graphRAG.generation.tool_response_formater import format_tool_results
from agents.graphRAG.generation.workflow_response_formater import format_workflow_results

logger = logging.getLogger(__name__)


class LLMAnswerGenerator:
    def generate(self, query, intent, tools=None, workflows=None):
        tools = tools or []
        workflows = workflows or []

        results = []

        if intent in ["tool", "both"] and tools:
            results.extend(format_tool_results(tools)["results"])
        if intent in ["workflow", "both"] and workflows:
            results.extend(format_workflow_results(workflows)["results"])

        return {"results": results}
