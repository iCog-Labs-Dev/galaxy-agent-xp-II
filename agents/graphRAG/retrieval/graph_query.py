from typing import Optional, List, Any, Dict
from neo4j import Session
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class GraphQueries:
    """Predefined parameterized queries and safe execution methods for Galaxy workflows, tools, and GraphRAG."""

    # -----------------------
    # Tool Queries
    # -----------------------
    @staticmethod
    def get_tool_by_id_query() -> str:
        return """
        MATCH (t:Tool {tool_id: $tool_id})
        RETURN t.tool_id AS tool_id, t.name AS name, t.version AS version, t.description AS description
        """

    @staticmethod
    def get_tool_with_inputs_outputs_query() -> str:
        return """
        MATCH (t:Tool {tool_id: $tool_id})
        OPTIONAL MATCH (t)-[:TOOL_HAS_INPUT]->(i:ToolInput)
        OPTIONAL MATCH (t)-[:TOOL_HAS_OUTPUT]->(o:ToolOutput)
        RETURN t.tool_id AS tool_id, t.name AS name,
               collect(DISTINCT i.name) AS inputs,
               collect(DISTINCT o.name) AS outputs
        """

    # -----------------------
    # Category Queries
    # -----------------------
    @staticmethod
    def get_tools_by_category_query() -> str:
        return """
        MATCH (c:ToolCategory {name: $category_name})<-[:BELONGS_TO]-(t:Tool)
        RETURN t.tool_id AS tool_id, t.name AS name, t.version AS version
        """

    # -----------------------
    # Workflow Queries
    # -----------------------
    @staticmethod
    def get_workflow_by_id_query() -> str:
        return """
        MATCH (w:Workflow {workflow_id: $workflow_id})
        RETURN w.workflow_id AS workflow_id, w.name AS name, w.category AS category, w.number_of_steps AS steps
        """

    @staticmethod
    def get_workflow_steps_query() -> str:
        return """
        MATCH (w:Workflow {workflow_id: $workflow_id})-[:HAS_STEP]->(s:Step)
        OPTIONAL MATCH (s)-[:STEP_REQUIRES]->(i:Input)
        OPTIONAL MATCH (s)-[:STEP_GENERATES]->(o:Output)
        RETURN s.step_uid AS step_uid, s.name AS step_name, s.tool_id AS tool_id,
               collect(DISTINCT i.name) AS inputs,
               collect(DISTINCT o.name) AS outputs
        ORDER BY s.step_uid
        """

    @staticmethod
    def get_workflow_inputs_outputs_query() -> str:
        return """
        MATCH (w:Workflow {workflow_id: $workflow_id})
        OPTIONAL MATCH (w)-[:REQUIRES]->(i:Input)
        OPTIONAL MATCH (w)-[:GENERATES]->(o:Output)
        RETURN collect(DISTINCT i.name) AS workflow_inputs,
               collect(DISTINCT o.name) AS workflow_outputs
        """

    # -----------------------
    # Relationship Queries
    # -----------------------
    @staticmethod
    def get_tool_category_relationship_query() -> str:
        return """
        MATCH (t:Tool {tool_id: $tool_id})-[:BELONGS_TO]->(c:ToolCategory)
        RETURN t.tool_id AS tool_id, c.name AS category_name
        """

    @staticmethod
    def get_step_tool_relationship_query() -> str:
        return """
        MATCH (s:Step {step_uid: $step_uid})
        RETURN s.step_uid AS step_uid, s.tool_id AS tool_id, s.tool_version AS tool_version
        """

    # -----------------------
    # Advanced / Optional
    # -----------------------
    @staticmethod
    def search_nodes_by_name_query(limit: int = 50) -> str:
        return f"""
        MATCH (n)
        WHERE toLower(n.name) CONTAINS toLower($name)
        RETURN n.name AS name, labels(n) AS labels, n
        LIMIT {limit}
        """

    # -----------------------
    # Wrapper / Execution Method
    # -----------------------
    @staticmethod
    def run_query(session: Session, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Safely execute a query using a Neo4j session with error handling.
        Returns a list of dictionaries for easy access.
        """
        parameters = parameters or {}
        try:
            result = session.run(query, **parameters)
            records = [dict(record) for record in result]
            logger.info(f"Query executed successfully: {query.strip().splitlines()[0]} ...")
            return records
        except Exception as e:
            logger.error(f"Failed to execute query: {query.strip().splitlines()[0]} | Error: {e}")
            return []

    # -----------------------
    # Convenience Method
    # -----------------------
    @staticmethod
    def fetch_single(session: Session, query: str, parameters: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Executes a query and returns a single record or None if empty.
        Useful for fetching one tool, workflow, or step.
        """
        results = GraphQueries.run_query(session, query, parameters)
        return results[0] if results else None
