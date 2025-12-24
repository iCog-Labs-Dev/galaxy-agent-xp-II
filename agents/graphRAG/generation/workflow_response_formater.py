import logging
from typing import List, Dict
from agents.summary_agent import summarize_workflow_suggestions

logger = logging.getLogger(__name__)


def format_workflow_results(workflows: List[Dict], query: str = "") -> Dict:
    results = []

    summarized_workflows = summarize_workflow_suggestions(workflows, query) if query and workflows else []

    for i, wf in enumerate(workflows):
        workflow = wf.get("workflow", wf)
        category = wf.get("category", {}) or workflow.get("category", "Unknown")

        try:
            score = round(float(wf.get("similarity_score", 0.0)), 4)
        except (TypeError, ValueError):
            score = 0.0

        readme = workflow.get("readme")

        if isinstance(readme, str):
            readme_excerpt = readme[:300]
        else:
            readme_excerpt = ""

        results.append({
            "name": workflow.get("name"),
            "category": category.get("name") if isinstance(category, dict) else category,
            "tools_used": wf.get("tools_used", []),
            "download_url": workflow.get("download_url"),
            "readme_excerpt": readme_excerpt,
            "score": score
        })

    return {"results": results}
