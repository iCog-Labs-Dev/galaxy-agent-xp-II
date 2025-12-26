# Galaxy Tool Community Detection & Semantic Summarization

## Overview
This module implements a **Global Hierarchical Clustering** engine for the Galaxy Tool Knowledge Graph. 

Unlike traditional categorization (which relies on static, manual labels), this system dynamically groups tools based on their **functional usage patterns** in real-world workflows. It detects "communities" of tools that are frequently used together and uses a Large Language Model (LLM) to generate semantic scientific titles and descriptions for these groups.

## 🎯 Purpose: Powering GraphRAG
This module is the backbone of the Agent's reasoning capabilities. It transforms a flat list of 5,000+ tools into a navigable map of science.

### Key Capabilities Enabled:
1.  **Global Search (The "Map"):** Allows the Agent to answer high-level questions (*"How do I analyze RNA-seq?"*) by finding the relevant "Theme" (Level 1 Community) rather than keyword-matching individual tools.
2.  **Contextual Recommendation:** By analyzing the topology of communities, the Agent can recommend the mathematically most probable "next tool" in a pipeline (e.g., suggesting *Bowtie2* after *Trimmomatic*).
3.  **Hallucination Control:** Communities act as semantic boundaries. When an Agent operates within a specific cluster (e.g., "Bacterial Assembly"), it is restricted to tools within that valid context.

---

## ⚙️ algorithmic Approach

### 1. Graph Projection (The "Used-With" Edge)
The raw Galaxy graph connects Workflows to Tools. We project this into a **Tool-Tool Co-occurrence Graph**.
*   **Strong Links:** Direct data flow (Tool A Output $\to$ Tool B Input).
*   **Weak Links:** Contextual co-occurrence (Tool A and Tool B appear in the same workflow).
*   **Normalization:** We enforce edge weights based on frequency, creating a Weighted Undirected Graph.

### 2. Hierarchical Leiden Algorithm
We use the **Leiden Algorithm** (an improvement on Louvain) to detect clusters. We implement a recursive 2-layer hierarchy:

| Level | Resolution ($\gamma$) | Description | Example |
| :--- | :--- | :--- | :--- |
| **L0 (Specific)** | `1.5` | High granularity. Groups tools performing a specific sub-task. | *"FastQ Quality Control"* |
| **L1 (Broad)** | `0.2` | Low granularity. Groups L0 clusters into broad scientific themes. | *"Genomics Pre-processing"* |

### 3. LLM Summarization
A raw cluster of IDs is meaningless to a human. We use an LLM (e.g., Qwen-72B, Llama-3) to semantically label the communities.
*   **Centrality-Based Context:** We select the top 15 tools by **Degree Centrality** to represent the cluster.
*   **Recursive Summarization:** L0 clusters are named based on their tools; L1 clusters are named based on their L0 children.
*   **Strict JSON:** The pipeline enforces strict JSON output for reliable database integration.

---

## 🚀 Usage

### Prerequisites
*   Neo4j Database running with Galaxy Data loaded.
*   Python 3.10+
*   HuggingFace API Token (for summarization).

### 1. Build Communities
Calculates topology and runs the Leiden algorithm.
```bash
python agents/community_detection/build_communities.py
```

### 2. Generate Summaries
Uses the LLM to title and describe the detected clusters.
```bash
python agents/community_detection/summarize_communities.py
```

---

## 📊 Visual Architecture
*See `diagrams/` folder for source files.*

### Data Pipeline
The flow from raw workflow data to a semantic knowledge graph.
![Pipeline](diagrams/pipeline_flow.mmd)

### Hierarchical Logic
How tools map to specific tasks (L0) and broader themes (L1).
![Hierarchy](diagrams/hierarchy_logic.mmd)
