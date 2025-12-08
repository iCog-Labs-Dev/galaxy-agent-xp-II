# test_graph_queries.py

from agents.ingestion.Load.neo4j_client import Neo4jClient
from agents.graphRAG.retrieval.graph_query import GraphQueries

neo = Neo4jClient(uri="bolt://localhost:7687", user="neo4j", password="password")

with neo.driver.session() as session:
    query = "MATCH (n) RETURN count(n) AS total LIMIT 1"
    try:
        result = GraphQueries.run_query(session, query)
        print("✔ GraphQueries works! Total nodes:", result)
    except Exception as e:
        print("❌ GraphQueries failed:", e)

neo.close()
