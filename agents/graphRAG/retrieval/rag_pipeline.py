from agents.graphRAG.retrieval.gemini_llm import GeminiLLM

def init_rag_pipeline(llm: GeminiLLM):
    """Initialize GraphRAG wrapper."""
    return GraphRAGLLMWrapper(llm)


class GraphRAGLLMWrapper:
    """LLM wrapper to generate Cypher + answer."""

    def __init__(self, llm):
        self.llm = llm

    def search(self, query_text: str):
        prompt = f"""
Convert the following natural language query to Cypher first, then provide the answer.

Query: {query_text}

Format:
Cypher: <your Cypher query here>
Answer: <answer here>
"""
        llm_output = self.llm.generate(prompt)
        cypher, answer = None, None

        # Parse LLM output
        if "Cypher:" in llm_output and "Answer:" in llm_output:
            try:
                cypher_part = llm_output.split("Cypher:")[1].split("Answer:")[0].strip()
                answer_part = llm_output.split("Answer:")[1].strip()
                # Remove markdown code block if present
                if cypher_part.startswith("```"):
                    cypher_part = "\n".join(cypher_part.splitlines()[1:-1])
                cypher, answer = cypher_part, answer_part
            except Exception as e:
                print(f"Error parsing LLM output: {e}")
        else:
            answer = llm_output.strip()

        return cypher, answer


def run_query(rag, query_text: str, session):
    """Generate Cypher from LLM and execute via GraphQueries."""
    cypher, llm_answer = rag.search(query_text)
    print("\n--- Query ---")
    print(query_text)

    if cypher:
        print("--- Generated Cypher ---")
        print(cypher)
        from agents.graphRAG.retrieval.graph_queries import GraphQueries
        records = GraphQueries.run_query(session, cypher)
        print("--- Answer ---")
        print(records if records else "No results found.")
        return records
    else:
        print("--- Answer (LLM only) ---")
        print(llm_answer)
        return llm_answer
