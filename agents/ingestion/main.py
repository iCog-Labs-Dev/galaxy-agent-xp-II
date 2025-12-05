import yaml
from Load.neo4j_client import Neo4jClient
from Load.wf_loader import GraphLoader
from Load.tool_loader import ToolLoader

# Helper to load YAML config
def load_config(path = "agents/graphRAG/config/graph_db_config.yml"):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def main():
    # Load Neo4j config from YAML
    config = load_config()
    neo_cfg = config["neo4j"]

    # Connect to Neo4j using config
    neo = Neo4jClient(
        uri=neo_cfg["uri"],
        user=neo_cfg["user"],
        password=neo_cfg["password"]
    )

    # Create indexes if configured
    if config.get("indexes", {}).get("create_on_start", False):
        try:
            neo.create_indexes()
        except Exception as e:
            print(f"Warning: failed to create indexes: {e}")

    # -----------------------
    # 1. Workflows ETL
    # -----------------------
    workflow_loader = GraphLoader(neo)
    workflow_loader.import_file(
        "utilities/workflow_downloader/data/galaxy_iwc_workflows_20251205_162934.json"
    )

    # -----------------------
    # 2. Tools ETL
    # -----------------------
    tool_loader = ToolLoader(neo)
    tool_loader.import_file(
        "utilities/tools_metadata_downloader/data/galaxy_instance_tools_2025-12-04_23-58-00.json"
    )

    # Close connection
    neo.close()
    print("Workflows ETL completed!")

if __name__ == "__main__":
    main()
