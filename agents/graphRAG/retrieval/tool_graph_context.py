import logging
from agents.ingestion.Load.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)
logging.getLogger("neo4j").setLevel(logging.WARNING)


class ToolGraphContext:
    """
    Production GraphRAG tool context retriever.

    Traversal:
        Tool
          ├─ Tool_HAS_INPUT → ToolInput
          └─ Tool_HAS_OUTPUT → ToolOutput
    """

    def __init__(self, neo_client: Neo4jClient):
        self.neo = neo_client

    def get_tool_context(self, tool_ids: list):
        if not tool_ids:
            logger.warning("Empty tool_ids provided")
            return []

        
        cypher = """
        MATCH (t:Tool)
        WHERE t.tool_id IN $tool_ids

        OPTIONAL MATCH (t)-[:Tool_HAS_INPUT]->(ti:ToolInput)
        OPTIONAL MATCH (t)-[:Tool_HAS_OUTPUT]->(to:ToolOutput)

        WITH t, collect(DISTINCT ti) AS inputs, collect(DISTINCT to) AS outputs
        RETURN t AS tool, inputs, outputs
        """

        try:
            records = self.neo.run_query(cypher, parameters={"tool_ids": tool_ids})
        except Exception:
            logger.exception("Failed to retrieve tool context")
            return []

        results = []
        for r in records:
            tool_node = self._clean(r.get("tool"))
            results.append({
                "tool": tool_node,
                "inputs": [self._clean(i) for i in r.get("inputs", []) if i],
                "outputs": [self._clean(o) for o in r.get("outputs", []) if o],
            })

        return results

    @staticmethod
    def _clean(node):
        """Return a clean dictionary representation of a Neo4j node."""
        if not node:
            return {}
        data = dict(node)
        data.pop("embedding", None)  # Remove embeddings from context
        return data
