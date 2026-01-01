"""
Create vector indexes for GraphRAG (Workflow, Step, Tool, Input, Output, Category).
Attempts both Neo4j 5.15+ syntax and 5.11–5.14 fallback syntax.
"""
import yaml
from neo4j import GraphDatabase
from pathlib import Path

# Point to graph-xp config (not graphRAG)
CONFIG_PATH = "agents/graph-xp/config/graph_db_config.yml"


def load_config(path: str) -> dict:
    """Load YAML config file."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def create_vector_indexes(driver):
    """Create vector indexes for all embedded node labels."""
    labels = [
        "Workflow",
        "Step",
        "Tool",
        "Input",
        "Output",
        "Category",
    ]

    def queries_for(label: str):
        lower = label.lower()
        # Neo4j 5.15+ (IF NOT EXISTS, similarityFunction)
        q_new = f"""
        CREATE VECTOR INDEX IF NOT EXISTS {lower}_embedding_index
        FOR (n:{label}) ON (n.embedding)
        OPTIONS {{ indexConfig: {{ `vector.dimensions`: 768, `vector.similarityFunction`: 'cosine' }} }}
        """
        # Neo4j 5.11–5.14 (no IF NOT EXISTS, similarity_function)
        q_old = f"""
        CREATE VECTOR INDEX {lower}_embedding_index
        FOR (n:{label}) ON (n.embedding)
        OPTIONS {{ indexConfig: {{ `vector.dimensions`: 768, `vector.similarity_function`: 'cosine' }} }}
        """
        return q_new, q_old

    with driver.session() as session:
        for label in labels:
            q_new, q_old = queries_for(label)
            try:
                session.run(q_new)
                print(f" Vector index ensured (new syntax) for {label}")
                continue
            except Exception as e_new:
                print(f"  New syntax failed for {label}: {e_new}")
            try:
                session.run(q_old)
                print(f" Vector index ensured (legacy syntax) for {label}")
            except Exception as e_old:
                print(f"  Legacy syntax failed for {label}: {e_old}")


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