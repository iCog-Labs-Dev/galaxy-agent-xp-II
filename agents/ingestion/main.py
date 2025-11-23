from Load.neo4j_client import Neo4jClient
from Load.wf_loader import GraphLoader
from Load.tool_loader import ToolLoader
from transform.tool_node_builder import ToolMetadataBuilder
from transform.tool_rel_builder import ToolMetadataRelations

def main():
    neo = Neo4jClient("bolt://localhost:7687", "neo4j", "password")

    # 1. Workflows ETL
    workflow_loader = GraphLoader(neo)
    workflow_loader.import_file("data/workflows.json")

    # 2. Tools ETL
    tool_builder = ToolMetadataBuilder()
    tool_rel_builder = ToolMetadataRelations()
    tool_loader = ToolLoader(neo, tool_builder, tool_rel_builder)
    tool_loader.import_file("data/tools.json")

    neo.close()

if __name__ == "__main__":
    main()
