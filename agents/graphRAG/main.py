from agents.ingestion.Load.neo4j_client import Neo4jClient
from agents.graphRAG.retrieval.gemini_llm import GeminiLLM
from agents.graphRAG.retrieval.rag_pipeline import init_rag_pipeline, run_query

def main():
    # 1. Connect to Neo4j
    neo4j_client = Neo4jClient(
        config_path="agents/graphRAG/config/graph_db_config.yml"
    )
    driver = neo4j_client.driver

    # 2. Initialize LLM
    llm = GeminiLLM(model_name="models/gemini-2.5-flash")

    # 3. Initialize GraphRAG pipeline
    rag = init_rag_pipeline(llm)

    # 4. Run queries
    queries = [
        "List all steps in the workflow 'Genome Assembly from Hifi reads with HiC phasing - VGP4' that use a tool from the category 'Get Data'"
    ]

    with driver.session() as session:
        for q in queries:
            run_query(rag, q, session)

    # 5. Close Neo4j
    neo4j_client.close()

if __name__ == "__main__":
    main()
