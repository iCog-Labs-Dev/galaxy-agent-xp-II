"""
Create vector indexes for GraphRAG (Tool + Workflow).
"""
import yaml
from neo4j import GraphDatabase
from pathlib import Path

CONFIG_PATH = "agents/graphRAG/config/graph_db_config.yml"


def load_config(path: str) -> dict:
    """Load YAML config file."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def create_vector_indexes(driver):
    """Create vector indexes for Tool and Workflow nodes."""
    queries = [
        # Tool vector index
        """
        CREATE VECTOR INDEX tool_embedding_index IF NOT EXISTS
        FOR (t:Tool)
        ON (t.embedding)
        OPTIONS {
          indexConfig: {
            `vector.dimensions`: 768,
            `vector.similarity_function`: 'cosine'
          }
        }
        """,
        # Workflow vector index
        """
        CREATE VECTOR INDEX workflow_embedding_index IF NOT EXISTS
        FOR (w:Workflow)
        ON (w.embedding)
        OPTIONS {
          indexConfig: {
            `vector.dimensions`: 768,
            `vector.similarity_function`: 'cosine'
          }
        }
        """
    ]

    with driver.session() as session:
        for q in queries:
            session.run(q)
            print(" Vector index ensured")


def main():
    print(" GraphRAG index initialization")

    config = load_config(CONFIG_PATH)

    # -----------------------------
    # Read config sections
    # -----------------------------
    neo_cfg = config.get("neo4j")
    if not neo_cfg:
        raise ValueError("Neo4j config missing in YAML")

    index_cfg = config.get("indexes", {})
    create_on_start = index_cfg.get("create_on_start", False)

    if not create_on_start:
        print("  Index creation skipped (indexes.create_on_start = false)")
        return

    print(" Index creation enabled by config")

    driver = GraphDatabase.driver(
        neo_cfg["uri"],
        auth=(neo_cfg["user"], neo_cfg["password"])
    )

    try:
        create_vector_indexes(driver)
        print(" All vector indexes created successfully")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
