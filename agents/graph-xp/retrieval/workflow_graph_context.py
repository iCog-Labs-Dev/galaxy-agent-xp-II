import logging
from typing import Any, Dict, List, Sequence

logger = logging.getLogger(__name__)
logging.getLogger("neo4j").setLevel(logging.WARNING)


class WorkflowGraphContext:
    """Retrieve workflow context using a generic Neo4j client (no ingestion dependency)."""

    def __init__(self, neo_client: Any):
        self.neo = neo_client

    def get_workflow_context(self, workflow_ids: list) -> List[Dict]:
        if not workflow_ids:
            logger.warning("Empty workflow_ids provided")
            return []

        cypher = """
        MATCH (w:Workflow)
        WHERE w.workflow_id IN $workflow_ids

        OPTIONAL MATCH (w)<-[:HAS_WORKFLOW]-(c:Category)
        OPTIONAL MATCH (w)-[:HAS_STEP]->(:Step)-[:STEP_USES_TOOL]->(t:Tool)
        OPTIONAL MATCH (w)-[:WORKFLOW_USES_TOOL]->(wt:Tool)

        WITH w, c,
             collect(DISTINCT t.name) AS step_tools,
             collect(DISTINCT wt.name) AS wf_tools

        WITH w, c, step_tools, wf_tools,
             coalesce(
                 w.workflow_name,
                 w.name,
                 CASE
                     WHEN w.file_name ENDS WITH '.ga' THEN left(w.file_name, size(w.file_name) - 3)
                     WHEN w.file_name ENDS WITH '.gxwf' THEN left(w.file_name, size(w.file_name) - 5)
                     WHEN w.file_name ENDS WITH '.json' THEN left(w.file_name, size(w.file_name) - 5)
                     ELSE w.file_name
                 END,
                 w.workflow_repository,
                 w.workflow_id
             ) AS display_name

        RETURN
            w {
                .workflow_id,
                .workflow_name,
                .name,
                .workflow_repository,
                .file_name,
                .raw_download_url,
                .readme_content,
                display_name: display_name
            } AS workflow,
            c { .category, .category_id } AS category,
            [tool IN step_tools WHERE tool IS NOT NULL] + [tool IN wf_tools WHERE tool IS NOT NULL] AS tools_used
        """

        try:
            records = self._run_query(
                cypher,
                parameters={"workflow_ids": workflow_ids}
            )
        except Exception:
            logger.exception("Failed to retrieve workflow context")
            return []

        results = []
        for r in records:
            workflow_val = r.get("workflow") if isinstance(r, Dict) else r["workflow"]
            category_val = r.get("category") if isinstance(r, Dict) else r["category"]
            tools_val = r.get("tools_used") if isinstance(r, Dict) else r["tools_used"]

            results.append({
                "workflow": workflow_val or {},
                "category": category_val or {},
                "tools_used": tools_val or [],
            })

        return results

    def _run_query(self, cypher: str, parameters: Dict[str, Any] | None = None) -> Sequence[Dict[str, Any]]:
        """Run a Cypher query using the available Neo4j client interface."""

        if hasattr(self.neo, "run_query"):
            return self.neo.run_query(cypher, parameters=parameters or {})  # type: ignore[attr-defined]

        if hasattr(self.neo, "driver"):
            with self.neo.driver.session() as session:  # type: ignore[attr-defined]
                result = session.run(cypher, **(parameters or {}))
                return [dict(rec) for rec in result]

        raise AttributeError("Neo4j client does not expose run_query or driver")