import yaml
from Load.neo4j_client import Neo4jClient
from Load.wf_loader import GraphLoader
from Load.tool_loader import ToolLoader
from tqdm import tqdm

def load_config(path="agents/graphRAG/config/graph_db_config.yml"):
    """Load Neo4j configuration from YAML file."""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def main():
    print("🚀 Starting ETL process...")

    # Load configuration
    config = load_config()
    
    # Connect to Neo4j
    print("🔌 Connecting to Neo4j...")
    neo = Neo4jClient(config_path="agents/graphRAG/config/graph_db_config.yml")

    # Optional: create indexes if specified in config
    if config.get("indexes", {}).get("create_on_start", False):
        print("📊 Creating indexes...")
        try:
            neo.create_indexes()
            print("✅ Indexes created")
        except Exception as e:
            print(f"⚠️ Warning: failed to create indexes: {e}")

    # -----------------------
    # 1. Workflows ETL
    # -----------------------
    print("📥 Loading workflows...")
    workflow_loader = GraphLoader(neo)
    workflow_loader.import_file(
        "embeddings/workflow_metadata_with_embeddings_20251220_000757.json"
    )
    print("✅ Workflows ETL completed!")

    # -----------------------
    # 2. Tools ETL
    # -----------------------
    print("📥 Loading tools...")
    tool_loader = ToolLoader(neo)
    tool_loader.import_file(
        "embeddings/tool_metadata_with_embeddings_20251220_122958.json"
    )
    print("✅ Tools ETL completed!")

    # Close Neo4j connection
    neo.close()
    print("🎉 ETL process finished successfully!")

if __name__ == "__main__":
    main()
