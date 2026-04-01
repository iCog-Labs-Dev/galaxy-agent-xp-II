from typing import List, Dict
from agents.summary_agent import SummaryAgent


# Deduplication 
def deduplicate_tools(tools: List[Dict]) -> List[Dict]:
    seen = {}

    for tool in tools:
        tool_node = tool.get("tool", tool)
        name = tool_node.get("name")
        score = tool.get("similarity_score", 0.0)

        if name not in seen or score > seen[name]["similarity_score"]:
            seen[name] = tool

    return list(seen.values())


# Formatter
def format_tool_results(tools: List[Dict], query: str = "") -> Dict:
    if not tools:
        return {"results": []}

    # Deduplicate first
    tools = deduplicate_tools(tools)

    # Summarize using unified SummaryAgent
    summary_agent = SummaryAgent()
    summary_text = (
        summary_agent.summarize_tools_suggestions(
            [t.get("tool", t) for t in tools],
            query
        )
        if query
        else None
    )

    results = []

    for tool in tools:
        tool_node = tool.get("tool", tool)
        results.append({
            "id": tool_node.get("id") or tool_node.get("tool_id"),
            "name": tool_node.get("name"),
            "description": tool_node.get("description"),
            "help": tool_node.get("help"),
            "version": tool_node.get("version"),
            "score": round(tool.get("similarity_score", 0.0), 4),
        })

    return {
        "results": results,
        "summary": summary_text
    }