
import os
import sys
from pathlib import Path

# ensure project root is on sys.path so `agents` package can be imported
project_root = str(Path(__file__).resolve().parents[2])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agents.graphRAG.pipeline.tool_retrieval_pipeline import ToolRetrievalPipeline
from agents.scripts.query_embedding import QueryEmbeddingService
from agents.ingestion.Load.neo4j_client import Neo4jClient

neo = Neo4jClient()
embedder = QueryEmbeddingService()
pipeline = ToolRetrievalPipeline(neo, embedder)

query = "quality control tool for sequencing data"
tools = pipeline.retrieve_tools(query, top_k=5)

for tool in tools:
    print(f"Tool: {tool['tool'].get('name')}, Score: {tool['similarity_score']:.4f}")
    print(f"  Category: {tool['category'].get('name')}")
    print(f"  Description: {tool['tool'].get('description', '')[:100]}...")
    
    inputs = [i.get('name') for i in tool.get('inputs', []) if i.get('name')]
    outputs = [o.get('name') for o in tool.get('outputs', []) if o.get('name')]
    
    print(f"  Inputs: {inputs[:5]}")  # Show first 5
    print(f"  Outputs: {outputs[:5]}")  # Show first 5
    print("------")

