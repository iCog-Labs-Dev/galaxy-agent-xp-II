import logging
from typing import Dict, List

from summary_agent import summarize_workflow_suggestions

logger = logging.getLogger(__name__)


def format_workflow_results(workflows: List[Dict], query: str = "") -> Dict:
    results = []
    summary_text = summarize_workflow_suggestions(workflows, query) if query and workflows else None

    for i, wf in enumerate(workflows):
        workflow = wf.get("workflow", wf) or {}
        category = wf.get("category", {}) or workflow.get("category", {}) or {}

        try:
            score = round(float(wf.get("similarity_score", 0.0)), 4)
        except (TypeError, ValueError):
            score = 0.0

        readme = workflow.get("readme") or workflow.get("readme_content")
        readme_excerpt = readme[:300] if isinstance(readme, str) else ""

        name = (
            workflow.get("display_name")
            or workflow.get("name")
            or workflow.get("workflow_name")
            or workflow.get("workflow_id")
        )
        category_text = None
        if isinstance(category, dict):
            category_text = category.get("category") or category.get("name")
        else:
            category_text = category
        category_text = category_text or "Unknown"

        results.append({
            "name": name or "Unknown",
            "category": category_text,
            "tools_used": wf.get("tools_used", []),
            "download_url": workflow.get("download_url") or workflow.get("raw_download_url"),
            "readme_excerpt": readme_excerpt,
            "score": score
        })

    return {"results": results, "summary": summary_text}