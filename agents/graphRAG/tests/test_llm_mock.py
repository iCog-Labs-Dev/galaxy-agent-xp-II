import pytest
from unittest.mock import patch, MagicMock
from agents.graphRAG.retrieval.gemini_llm import GeminiLLM
from agents.graphRAG.pipeline.rag_pipeline import GraphRAGPipeline
from agents.ingestion.Load.neo4j_client import Neo4jClient

@pytest.fixture
def mock_gemini():
    with patch.object(GeminiLLM, "generate", return_value="Cypher: MATCH (n) RETURN n\nAnswer: 42 nodes") as mock:
        yield mock

def test_llm_generation_with_mock(mock_gemini):
    client = Neo4jClient()
    llm = GeminiLLM()
    pipeline = GraphRAGPipeline(client.driver, llm)

    query = "Count all nodes"
    cypher, answer = pipeline.generate_cypher(query)
    assert "MATCH (n) RETURN n" in cypher
    assert "42 nodes" in answer
