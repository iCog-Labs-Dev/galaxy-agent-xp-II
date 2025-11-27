from Load.neo4j_client import Neo4jClient
from Load.wf_loader import GraphLoader
# from Load.tool_loader import ToolLoader
# from transform.tool_node_builder import ToolMetadataBuilder
# from transform.tool_rel_builder import ToolMetadataRelations

def main():
    # Connect to Neo4j
    neo = Neo4jClient("bolt://localhost:7687", "neo4j", "abc12345")

    # -----------------------
    # 1. Workflows ETL
    # -----------------------
    workflow_loader = GraphLoader(neo)
    workflow_loader.import_file(
        "utilities/workflow_downloader/data/galaxy_iwc_workflows_20251127_093913.json"
    )

    # -----------------------
    # 2. Tools ETL (commented for now)
    # -----------------------
    # tool_builder = ToolMetadataBuilder()
    # tool_rel_builder = ToolMetadataRelations()
    # tool_loader = ToolLoader(neo, tool_builder, tool_rel_builder)
    # tool_loader.import_file(
    #     "agents/ingestion/test_data/preprocessed_tools_20250815_150209.json"
    # )

    # Close connection
    neo.close()
    print("Workflows ETL completed!")

if __name__ == "__main__":
    main()
