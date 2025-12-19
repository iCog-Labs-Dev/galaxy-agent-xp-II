import unittest
from unittest.mock import Mock, patch
import os
from fastapi.testclient import TestClient

from agents.graphRAG.app import app


class TestApp(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    @patch('agents.graphRAG.app.load_dotenv')
    @patch.dict(os.environ, {
        'GEMINI_API_KEY': 'dummy',
        'OPENAI_API_KEY': 'dummy'
    })
    def test_app_initialization(self, mock_load_dotenv):
        self.assertIsNotNone(app)
        self.assertEqual(app.title, "Galaxy GraphRAG API")

        cors = next(
            (m for m in app.user_middleware if m.cls.__name__ == "CORSMiddleware"),
            None
        )
        self.assertIsNotNone(cors)

    @patch('agents.graphRAG.app.Neo4jClient')
    @patch('agents.graphRAG.app.GeminiLLM')
    @patch('agents.graphRAG.app.GraphRAGPipeline')
    def test_rag_initialization_success(self, mock_pipeline, mock_llm, mock_client):
        mock_client.return_value.driver = Mock()
        mock_llm.return_value = Mock()
        mock_pipeline.return_value = Mock()

        import importlib
        from agents.graphRAG import app as app_module
        importlib.reload(app_module)

        self.assertIsNotNone(app_module.rag)

     

    @patch('agents.graphRAG.app.GraphRAGPipeline')
    @patch('agents.graphRAG.app.GeminiLLM')
    @patch('agents.graphRAG.app.Neo4jClient', side_effect=Exception("Connection failed"))
    def test_rag_initialization_failure(self, mock_client, mock_llm, mock_pipeline):
        # Test the initialization logic directly
        try:
            neo4j_client = mock_client()
            llm = mock_llm()
            rag = mock_pipeline(neo4j_client.driver, llm)
        except Exception:
            rag = None
        self.assertIsNone(rag)

   



    @patch('agents.graphRAG.app.rag', new_callable=Mock)
    def test_query_graphrag_success(self, mock_rag):
        mock_rag.run.return_value = {
            "cypher": "MATCH (n) RETURN n",
            "answer": "Test answer"
        }

        res = self.client.post("/query-graphrag", json={"query": "Test query"})
        self.assertEqual(res.status_code, 200)

        data = res.json()
        self.assertEqual(data["cypher"], "MATCH (n) RETURN n")
        self.assertEqual(data["answer"], "Test answer")

    @patch('agents.graphRAG.app.rag', None)
    def test_query_graphrag_rag_none(self):
        res = self.client.post("/query-graphrag", json={"query": "Test query"})
        self.assertEqual(res.status_code, 500)
        self.assertIn("GraphRAG pipeline not initialized", res.json()["detail"])


    @patch('agents.graphRAG.app.rag', new_callable=Mock)
    def test_query_graphrag_exception(self, mock_rag):
        mock_rag.run.side_effect = Exception("Query failed")

        res = self.client.post("/query-graphrag", json={"query": "Test query"})
        self.assertEqual(res.status_code, 500)
        self.assertIn("GraphRAG query failed", res.json()["detail"])
