from agents.ingestion.Load.neo4j_client import Neo4jClient

# Uses the default config YAML
neo = Neo4jClient()  

# Or explicitly point to the YAML file
# neo = Neo4jClient(config_path="agents/graphRAG/config/graph_db_config.yml")

# Test a query
with neo.driver.session() as session:
    result = session.run("MATCH (n) RETURN labels(n), n LIMIT 10")
    for record in result:
        print(record)

neo.close()
