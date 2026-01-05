import logging
from typing import Any, Dict, List, Sequence

logger = logging.getLogger(__name__)
logging.getLogger("neo4j").setLevel(logging.WARNING)


class ToolGraphContext:
    """GraphRAG tool context retriever using generic Neo4j client.

    Traversal:
        Tool
          ├─ Tool_HAS_INPUT → ToolInput
          └─ Tool_HAS_OUTPUT → ToolOutput
    """

    def __init__(self, neo_client: Any):
        self.neo = neo_client

    def get_tool_context(self, tool_ids: list):
        if not tool_ids:
            logger.warning("Empty tool_ids provided")
            return []

        cypher = """
        MATCH (t:Tool)
        WHERE t.tool_id IN $tool_ids

        OPTIONAL MATCH (t)-[:TOOL_HAS_INPUT]->(ti:ToolInput)
        OPTIONAL MATCH (t)-[:TOOL_HAS_OUTPUT]->(to:ToolOutput)

        WITH t,
             [n IN collect(DISTINCT ti) WHERE n IS NOT NULL] AS inputs,
             [n IN collect(DISTINCT to) WHERE n IS NOT NULL] AS outputs,
             coalesce(t.tool_name, t.name, t.id, t.tool_id) AS display_name

        RETURN
            t {.*, display_name: display_name} AS tool,
            inputs,
            outputs
        """

        try:
            records = self._run_query(cypher, parameters={"tool_ids": tool_ids})
        except Exception:
            logger.exception("Failed to retrieve tool context")
            return []

        results = []
        for r in records:
            tool_node = self._clean(r.get("tool")) if isinstance(r, Dict) else self._clean(r["tool"])
            inputs = r.get("inputs", []) if isinstance(r, Dict) else r["inputs"]
            outputs = r.get("outputs", []) if isinstance(r, Dict) else r["outputs"]
            results.append({
                "tool": tool_node,
                "inputs": [self._clean(i) for i in inputs if i],
                "outputs": [self._clean(o) for o in outputs if o],
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

    @staticmethod
    def _clean(node):
        """Return a clean dictionary representation of tools of a Neo4j node."""
        if not node:
            return {}
        data = dict(node)
        data.pop("embedding", None)  
        return data