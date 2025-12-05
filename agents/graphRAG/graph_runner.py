# agents/graphRAG/graph_runner.py
from typing import Optional, List, Any, Dict
from agents.ingestion.Load.neo4j_client import Neo4jClient
from agents.graphRAG.retrieval.graph_query import GraphQueries
import logging

# -----------------------
# Logging Setup
# -----------------------
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class GraphRunner:
    """
    A professional wrapper to execute GraphQueries on Neo4jClient safely.
    Provides methods for fetching single or multiple records with full error handling.
    """

    def __init__(self, neo: Neo4jClient):
        self.neo = neo

    def run(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute any Cypher query via Neo4jClient.
        Returns a list of dictionaries with query results.
        """
        parameters = parameters or {}
        try:
            with self.neo.driver.session() as session:
                results = GraphQueries.run_query(session, query, parameters)
                logger.info(f"Query returned {len(results)} records.")
                return results
        except Exception as e:
            logger.error(f"Failed to run query: {query.strip().splitlines()[0]} | Error: {e}")
            return []

    def fetch_single(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Execute a query and return a single record or None.
        """
        results = self.run(query, parameters)
        return results[0] if results else None

# -----------------------
# Example Usage
# -----------------------
if __name__ == "__main__":
    neo = Neo4jClient("bolt://localhost:7687", "neo4j", "password")
    runner = GraphRunner(neo)

    # Fetch a single tool by tool_id
    tool_id = "TOOL_123"
    tool = runner.fetch_single(GraphQueries.get_tool_by_id_query(), {"tool_id": tool_id})
    print(f"Tool: {tool}")

    # Fetch all tools in a category
    category_name = "Alignment"
    tools = runner.run(GraphQueries.get_tools_by_category_query(), {"category_name": category_name})
    print(f"Tools in '{category_name}': {tools}")

    # Close connection
    neo.close()
