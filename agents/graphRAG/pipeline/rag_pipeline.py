import json
from typing import Optional, Tuple, List, Dict
import time
import logging
from pathlib import Path

from agents.graphRAG.retrieval.gemini_llm import GeminiLLM
from agents.graphRAG.retrieval.graph_queries import GraphQueries
from agents.graphRAG.retrieval.retriever_setup import init_retriever

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# ---------------- HELPER ---------------- #
def load_schema(schema_file: str) -> Tuple[Dict, Dict]:
    """
    Load Neo4j schema JSON and split into nodes and relationships.
    """
    path = Path(schema_file).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_file}")
    
    with open(path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    
    nodes = schema.get("nodes", {})
    relationships = schema.get("relationships", {})
    
    if not nodes or not relationships:
        logger.warning("Schema loaded but nodes or relationships are empty.")
    
    return nodes, relationships


# ---------------- INITIALIZER ---------------- #
def init_rag_pipeline(driver, llm: GeminiLLM, schema_file: str) -> "GraphRAGPipeline":
    """
    Factory method to initialize the GraphRAG pipeline with schema loaded from file.
    """
    nodes, relationships = load_schema(schema_file)
    return GraphRAGPipeline(driver, llm, nodes, relationships)


# ---------------- PIPELINE ---------------- #
class GraphRAGPipeline:
    """
    GraphRAG pipeline with schema-aware Cypher generation.
    """

    def __init__(self, driver, llm, schema_nodes: dict, schema_rels: dict):
        """
        Args:
            driver: Neo4j driver/session
            llm: LLM wrapper, e.g., GeminiLLM
            schema_nodes: dict of Neo4j nodes schema
            schema_rels: dict of Neo4j relationships schema
        """
        self.driver = driver
        self.llm = llm
        self.schema_nodes = schema_nodes
        self.schema_rels = schema_rels

        # Initialize schema-aware retriever
        try:
            self.retriever = init_retriever(driver, llm)
        except Exception as e:
            logger.warning(f"Retriever initialization failed: {e}")
            self.retriever = None

    # ---------------- LLM STEP ---------------- #
    def generate_cypher(self, query_text: str) -> Tuple[Optional[str], Optional[str]]:
        nodes_json = json.dumps(self.schema_nodes, indent=2)
        rels_json = json.dumps(self.schema_rels, indent=2)

        prompt = f"""
You are a Neo4j expert assistant. Follow these rules strictly:

Rules:
1. Only use nodes and relationships in the schema.
2. Do not invent relationships or properties.
3. Only output valid Cypher.
4. Return the correct properties as specified for each relationship.
5. Do not add markdown or formatting.

Neo4j Schema:
Nodes:
{nodes_json}

Relationships:
{rels_json}

User Question:
{query_text}

Return format:
Cypher: <cypher query>
Answer: <brief natural language answer>
"""
        try:
            llm_output = self.llm.generate(prompt)
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return None, f"LLM error: {e}"

        # Parse output
        cypher, answer = None, None
        try:
            if "Cypher:" in llm_output and "Answer:" in llm_output:
                cypher = llm_output.split("Cypher:")[1].split("Answer:")[0].strip()
                answer = llm_output.split("Answer:")[1].strip()
            else:
                answer = llm_output.strip()
        except Exception as e:
            logger.error(f"Failed to parse LLM output: {e}")
            answer = llm_output.strip()

        return cypher, answer

    # ---------------- CYHER EXECUTION ---------------- #
    def execute_cypher(self, session, cypher: str) -> List[Dict]:
        try:
            return GraphQueries.run_query(session, cypher)
        except Exception as e:
            logger.error(f"Neo4j query failed: {e}")
            return []

    # ---------------- FULL PIPELINE ---------------- #
    def run(self, query_text: str) -> Dict:
        if not self.driver:
            raise RuntimeError("GraphRAG pipeline not initialized.")

        start_time = time.time()

        cypher, _ = self.generate_cypher(query_text)
        if not cypher:
            return {"cypher": None, "answer": "Unable to generate Cypher query."}

        records: List[Dict] = []
        try:
            with self.driver.session() as session:
                records = self.execute_cypher(session, cypher)
        except Exception as e:
            return {"cypher": cypher, "answer": f"Query execution failed: {e}"}

        try:
            result_prompt = f"""
You are a Neo4j assistant. Only use the data below to answer.

User Question: {query_text}
Cypher: {cypher}
Execution Result: {records}

Provide a concise answer containing ONLY the information asked by the user.
"""
            llm_answer = self.llm.generate(result_prompt).strip()
        except Exception:
            llm_answer = str(records)  # fallback

        latency_ms = (time.time() - start_time) * 1000

        return {
            "cypher": cypher,
            "answer": llm_answer,
            "latency_ms": latency_ms,
            "retrieved_count": len(records)
        }
