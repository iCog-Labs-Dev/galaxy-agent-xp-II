from typing import Optional, List, Any, Dict
from neo4j import Session
import logging
import time

logger = logging.getLogger(__name__)


class GraphQueries:
    """
    Centralized Neo4j Cypher query definitions and execution utilities.
    Designed for:
    - GraphRAG retrieval
    - FastAPI services
    - Testing & benchmarking
    """

  
    # TOOL QUERIES
    
    @staticmethod
    def tool_by_id() -> str:
        return """
        MATCH (t:Tool {tool_id: $tool_id})
        RETURN
            t.tool_id AS tool_id,
            t.name AS name,
            t.version AS version,
            t.description AS description
        """

    @staticmethod
    def tool_with_io() -> str:
        return """
        MATCH (t:Tool {tool_id: $tool_id})
        OPTIONAL MATCH (t)-[:TOOL_HAS_INPUT]->(i:ToolInput)
        OPTIONAL MATCH (t)-[:TOOL_HAS_OUTPUT]->(o:ToolOutput)
        RETURN
            t.tool_id AS tool_id,
            t.name AS name,
            collect(DISTINCT i.name) AS inputs,
            collect(DISTINCT o.name) AS outputs
        """

    # CATEGORY QUERIES
    @staticmethod
    def tools_by_category() -> str:
        return """
        MATCH (c:ToolCategory {name: $category_name})<-[:BELONGS_TO]-(t:Tool)
        RETURN
            t.tool_id AS tool_id,
            t.name AS name,
            t.version AS version
        """


    # WORKFLOW QUERIES
    @staticmethod
    def workflow_by_id() -> str:
        return """
        MATCH (w:Workflow {workflow_id: $workflow_id})
        RETURN
            w.workflow_id AS workflow_id,
            w.name AS name,
            w.category AS category,
            w.number_of_steps AS steps
        """

    @staticmethod
    def workflow_steps() -> str:
        return """
        MATCH (w:Workflow {workflow_id: $workflow_id})-[:HAS_STEP]->(s:Step)
        OPTIONAL MATCH (s)-[:STEP_REQUIRES]->(i:Input)
        OPTIONAL MATCH (s)-[:STEP_GENERATES]->(o:Output)
        RETURN
            s.step_uid AS step_uid,
            s.name AS step_name,
            s.tool_id AS tool_id,
            collect(DISTINCT i.name) AS inputs,
            collect(DISTINCT o.name) AS outputs
        ORDER BY s.step_uid
        """
    @staticmethod
    def workflow_io() -> str:
        return """
        MATCH (w:Workflow {workflow_id: $workflow_id})
        OPTIONAL MATCH (w)-[:REQUIRES]->(i:Input)
        OPTIONAL MATCH (w)-[:GENERATES]->(o:Output)
        RETURN
            collect(DISTINCT i.name) AS workflow_inputs,
            collect(DISTINCT o.name) AS workflow_outputs
        """

    # RELATIONSHIP QUERIES
    
    @staticmethod
    def tool_category() -> str:
        return """
        MATCH (t:Tool {tool_id: $tool_id})-[:BELONGS_TO]->(c:ToolCategory)
        RETURN
            t.tool_id AS tool_id,
            c.name AS category_name
        """

    @staticmethod
    def step_tool() -> str:
        return """
        MATCH (s:Step {step_uid: $step_uid})
        RETURN
            s.step_uid AS step_uid,
            s.tool_id AS tool_id,
            s.tool_version AS tool_version
        """


    # GENERIC SEARCH (SAFE)
    @staticmethod
    def search_nodes_by_name() -> str:
        return """
        MATCH (n)
        WHERE toLower(n.name) CONTAINS toLower($name)
        RETURN n.name AS name, labels(n) AS labels
        LIMIT $limit
        """

    # EXECUTION UTILITIES
    
    @staticmethod
    def run_query(
        session: Session,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        measure_time: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Executes a Cypher query safely.
        Optionally measures execution time (for benchmarking).
        """
        parameters = parameters or {}
        start = time.time()

        try:
            result = session.run(query, parameters)
            records = [dict(record) for record in result]

            if measure_time:
                latency_ms = (time.time() - start) * 1000
                logger.info(f"Query latency: {latency_ms:.2f} ms")

            return records

        except Exception as e:
            logger.error("Neo4j query execution failed", exc_info=e)
            return []

    @staticmethod
    def fetch_one(
        session: Session,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Returns exactly one record or None.
        """
        results = GraphQueries.run_query(session, query, parameters)
        return results[0] if results else None
