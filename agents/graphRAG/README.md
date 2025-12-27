# GraphRAG Module – Galaxy Agent XP-II

This module implements a **Hybrid GraphRAG pipeline** for recommending **Galaxy tools and workflows** using **Neo4j vector search combined with graph traversal**.

It is designed to be **deterministic**, **explainable**, and **production-ready**.

---

## Folder Structure

```text
agents/graphRAG/
│
├── config/
│   └── graph_db_config.yml
│
├── generation/
│   ├── answer_generator.py
│   ├── tool_response_formater.py
│   └── workflow_response_formater.py
│
├── pipeline/
│   ├── hybrid_rag_pipeline.py
│   ├── tool_retrieval_pipeline.py
│   └── workflow_retrival_pipeline.py
│
├── retrieval/
│   ├── tool_vector_search.py
│   ├── workflow_vector_search.py
│   ├── tool_graph_context.py
│   └── workflow_graph_context.py
│
├── scripts/
│   └── create_vector_indexes.py
│
├── tests/
├── benchmarks/
└── README.md
```

---

## What This Module Does

* Stores vector embeddings directly on **Neo4j nodes**
* Performs **vector similarity search** using Neo4j indexes
* Expands matched results using **graph relationships**
* Returns clean, structured **JSON tool and workflow recommendations**

---

## End-to-End Query Flow

```text
User Query
   ↓
Intent Classification
   ↓
Query Embedding (BAAI/bge-base-en-v1.5)
   ↓
Neo4j Vector Search
   ↓
Matched Entity IDs
   ↓
Graph Context Expansion
   ↓
Structured Results (JSON)
```

---

## Key Components

### 1️ Retrieval Layer (`retrieval/`)

Handles **vector search** and **graph traversal**.

* **tool_vector_search.py**
  Performs vector similarity search over *Tool* embeddings

* **workflow_vector_search.py**
  Performs vector similarity search over *Workflow* embeddings

* **tool_graph_context.py**
  Expands context: Tool → Category → Inputs → Outputs

* **workflow_graph_context.py**
  Expands context: Workflow → Steps → Tools

---

### 2️ Pipeline Layer (`pipeline/`)

Orchestrates the full retrieval flow.

* **hybrid_rag_pipeline.py**
  Main entry point that routes queries to tool or workflow pipelines

* **tool_retrieval_pipeline.py**
  Tool-only retrieval logic

* **workflow_retrival_pipeline.py**
  Workflow-only retrieval logic

---

### 3️ Generation Layer (`generation/`)

Formats deterministic API responses.

* **tool_response_formater.py**
  Outputs tool results in the format:

```json
{
  "results": [
    { "id": "", "name": "", "description": "", "category": "", "score": 0.0 }
  ]
}
```

* **workflow_response_formater.py**
  Outputs workflow results in the format:

```json
{
  "results": [
    { "name": "", "category": "", "download_url": "", "score": 0.0 }
  ]
}
```

* **answer_generator.py**
  Deterministic response builder (no hallucinations)

---

### 4️ Scripts (`scripts/`)

* **create_vector_indexes.py**
  Creates Neo4j vector indexes for stored embeddings

> This script should be run **once after data ingestion**.

---

## Neo4j Configuration

Edit the following file:

```text
agents/graphRAG/config/graph_db_config.yml
```

Example configuration:

```yaml
neo4j:
  uri: bolt://localhost:7687
  user: neo4j
  password: your_password
```

---

## API Output (Guaranteed Format)

### Tool Query Example

```json
{
  "results": [
    {
      "id": "toolshed.g2.bx.psu.edu/repos/devteam/bwa/bwa_mem/0.7.17.2",
      "name": "BWA-MEM",
      "description": "Align sequences to a reference genome",
      "category": "Alignment",
      "score": 0.92
    }
  ]
}
```

---

### Workflow Query Example

```json
{
  "results": [
    {
      "name": "bacterial-genome-assembly",
      "category": "genome-assembly",
      "download_url": "https://raw.githubusercontent.com/galaxyproject/iwc/main/workflows/genome-assembly/bacterial-genome-assembly/bacterial_genome_assembly.ga",
      "readme_excerpt": "Bacterial genome assembly workflow for paired end data...",
      "score": 0.82
    }
  ]
}
```
