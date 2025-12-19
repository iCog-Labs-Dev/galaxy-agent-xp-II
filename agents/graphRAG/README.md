#  GraphRAG Pipeline - Galaxy Agent XP-II

## Overview
GraphRAG integrates **Neo4j knowledge graphs** with **retrieval-augmented generation (RAG)** for intelligent querying of Galaxy tools and workflows.  
It provides:

- Semantic retrieval from Neo4j graph
- LLM-assisted answers
- Benchmarking metrics (recall@k, precision@k, latency)
- FastAPI endpoints for programmatic access

---

##  Pipeline Components

### 1. GraphRAG Pipeline
- File: `agents/graphRAG/pipeline/rag_pipeline.py`
- Combines **Neo4j queries** + **LLM**.
- Returns structured answers with optional fallback to LLM generation.

### 2. Graph Queries
- File: `agents/graphRAG/retrieval/graph_queries.py`
- Predefined Cypher queries:
  - Tools, workflows, categories, relationships
  - Safe execution: `run_query()`, `fetch_one()`

### 3. LLM Retriever
- File: `agents/graphRAG/retrieval/gemini_llm.py`
- Supports **Google Gemini** or other LLMs
- Generates context-aware answers from graph retrieval

---

##  Running the API
```bash
uvicorn agents.graphRAG.app:app --reload

