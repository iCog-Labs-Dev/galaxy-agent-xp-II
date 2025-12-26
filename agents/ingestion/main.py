from Load.neo4j_client import Neo4jClient
from Load.wf_loader import GraphLoader
from Load.tool_loader import ToolLoader
# builder and rel_builder are created inside ToolLoader

def main():
    # Connect to Neo4j
    neo = Neo4jClient("bolt://localhost:7687", "neo4j", "abc12345")

    # Create indexes to speed up lookups for tools and related nodes
    try:
        neo.create_indexes()
    except Exception as e:
        print(f"Warning: failed to create indexes: {e}")

    # -----------------------
    # 1. Workflows ETL
    # -----------------------
    workflow_loader = GraphLoader(neo)
    workflow_loader.import_file(
        "utilities/workflow_downloader/data/iwc_full_20251220_214925.json"
    )

    # -----------------------
    # 2. Tools ETL (commented for now)
    # -----------------------
    # Tools ETL: load tool metadata into the graph
    tool_loader = ToolLoader(neo)
    tool_loader.import_file(
        "utilities/tools_metadata_downloader/data/preprocessed_tools_20251220_211654.json"
    )

    # Close connection
    neo.close()
    print("Workflows ETL completed!")

if __name__ == "__main__":
    main()
