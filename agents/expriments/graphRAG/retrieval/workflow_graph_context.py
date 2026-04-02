import logging
from typing import List, Dict
from agents.ingestion.Load.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)
logging.getLogger("neo4j").setLevel(logging.WARNING)


class WorkflowGraphContext:
    """Retrieve full workflow context for given workflow_ids from the output of vector search."""

    def __init__(self, neo_client: Neo4jClient):
        self.neo = neo_client

    def get_workflow_context(self, workflow_ids: list) -> List[Dict]:
        if not workflow_ids:
            logger.warning("Empty workflow_ids provided")
            return []

        cypher = """
        MATCH (w:Workflow)
        WHERE w.workflow_id IN $workflow_ids

        OPTIONAL MATCH (w)-[:BELONGS_TO]->(c:Category)
        OPTIONAL MATCH (w)-[:HAS_STEP]->(:Step)-[:USES_TOOL]->(t:Tool)

        RETURN
            w {
                .workflow_id,
                .name,
                .readme,
                .download_url
            } AS workflow,
            c { .name } AS category,
            collect(DISTINCT t.name) AS tools_used
        """

        try:
            records = self.neo.run_query(
                cypher,
                parameters={"workflow_ids": workflow_ids}
            )
        except Exception:
            logger.exception("Failed to retrieve workflow context")
            return []

        results = []
        for r in records:
            results.append({
                "workflow": r.get("workflow", {}),
                "category": r.get("category", {}),
                "tools_used": r.get("tools_used", []),
            })

        return results