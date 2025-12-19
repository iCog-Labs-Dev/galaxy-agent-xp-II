# agents/tests/test_graphrag_pipeline.py
import json
import pytest
from agents.graphRAG.pipeline.rag_pipeline import GraphRAGPipeline
from agents.graphRAG.retrieval.gemini_llm import GeminiLLM
from agents.ingestion.Load.neo4j_client import Neo4jClient

# ---------------- FIXTURE ---------------- #
@pytest.fixture(scope="module")
def rag_pipeline():
    """
    Initialize the GraphRAG pipeline once per module.
    """
    neo4j_client = Neo4jClient()
    llm = GeminiLLM()
    return GraphRAGPipeline(neo4j_client.driver, llm)

# ---------------- TEST FUNCTION ---------------- #
def run_pipeline_tests(rag_pipeline, test_file_path):
    """
    Load test cases from JSON and run them through the pipeline.
    """
    with open(test_file_path, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    for case in test_cases:
        prompt = case["prompt"]
        expected = case.get("expected_answer")

        result = rag_pipeline.run(prompt)
        # Use executed records if available; fallback to LLM answer
        answer = result["records"] if result["records"] else result["llm_answer"]

        if expected:
            assert expected in str(answer), f"❌ FAIL | Query: '{prompt}' → Got: {answer}, Expected: {expected}"
            print(f"✅ PASS | Query: '{prompt}' → Answer contains expected info")
        else:
            print(f"ℹ️ Info | Query: '{prompt}' → Got: {answer}")

# ---------------- ENTRYPOINT ---------------- #
if __name__ == "__main__":
    # Initialize pipeline
    pipeline = rag_pipeline()
    # Run tests using selected JSON dataset
    run_pipeline_tests(pipeline, "agents/tests/data/test_data.json")
