import yaml
from neo4j import GraphDatabase

# Load Neo4j config
with open("agents/graphRAG/config/graph_db_config.yml", "r") as f:
    cfg = yaml.safe_load(f)

neo_cfg = cfg["neo4j"]

# Connect
driver = GraphDatabase.driver(
    neo_cfg["uri"],
    auth=(neo_cfg["user"], neo_cfg["password"])
)

# Test query
with driver.session() as session:
    result = session.run("RETURN 1 AS test")
    print("Connection successful:", result.single()["test"])

driver.close()
