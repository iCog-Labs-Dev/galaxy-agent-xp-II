
import os
import sys
from pathlib import Path

# ensure project root is on sys.path so `agents` package can be imported
project_root = str(Path(__file__).resolve().parents[2])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agents.graphRAG.pipeline.workflow_retrival_pipeline import WorkflowRetrievalPipeline
from agents.scripts.query_embedding import QueryEmbeddingService
from agents.ingestion.Load.neo4j_client import Neo4jClient
neo = Neo4jClient()

embedder = QueryEmbeddingService()
pipeline = WorkflowRetrievalPipeline(neo, embedder)

query = "RNA-seq quality control workflow"
workflows = pipeline.retrieve_workflows(query, top_k=5)

for wf in workflows:
    print(f"Workflow: {wf['workflow'].get('name')}, Score: {wf['similarity_score']:.4f}")
    print(f"  Category: {wf['category'].get('name')}")

    all_tools = set()
    all_inputs = set()
    all_outputs = set()

    for step in wf.get("steps", []):
        for t in step.get("tools", []):
            if t.get("name"):
                all_tools.add(t["name"])

        for i in step.get("inputs", []):
            if i.get("name"):
                all_inputs.add(i["name"])

        for o in step.get("outputs", []):
            if o.get("name"):
                all_outputs.add(o["name"])

    print(f"  Tools: {sorted(all_tools)}")
    print(f"  Inputs: {sorted(all_inputs)}")
    print(f"  Outputs: {sorted(all_outputs)}")
    print("------")
