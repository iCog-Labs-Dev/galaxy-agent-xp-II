"""Semantic similarity search over graph nodes using stored embeddings.

This script embeds a text query with the same model used in embed_nodes.py
and computes cosine similarity (dot product of normalized vectors) against
nodes' `embedding` property. Results are returned from Neo4j with scores.

Usage (from repo root):
  python agents/generic_loader/search.py \
    --label Step \
    --q "align sequences" \
    --k 10 \
    --uri bolt://localhost:7687 \
    --user neo4j \
    --password YOUR_PASSWORD
"""

import argparse
import logging
from typing import Any, Dict, List, Tuple

import numpy as np
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer

from schema_models import DEFAULT_CONFIG

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def id_prop_by_label() -> Dict[str, str]:
    return {spec.label: spec.id_property for spec in DEFAULT_CONFIG.nodes}


def fetch_workflow_details(driver, workflow_ids: List[Any]) -> Dict[Any, Dict[str, Any]]:
    if not workflow_ids:
        return {}
    q = (
        "MATCH (w:Workflow) WHERE w.workflow_id IN $ids\n"
        "OPTIONAL MATCH (w)-[:HAS_STEP]->(s:Step)\n"
        "OPTIONAL MATCH (s)-[:STEP_REQUIRES]->(i:Input)\n"
        "OPTIONAL MATCH (s)-[:STEP_GENERATES]->(o:Output)\n"
        "RETURN w.workflow_id AS id, w.workflow_repository AS repo, w.file_name AS file, w.category AS category, \n"
        "       w.number_of_steps AS num_steps, w.readme_content AS readme, \n"
        "       collect(DISTINCT i.name) AS inputs, collect(DISTINCT o.name) AS outputs"
    )
    out: Dict[Any, Dict[str, Any]] = {}
    with driver.session() as session:
        for rec in session.run(q, ids=workflow_ids):
            out[rec["id"]] = {
                "repo": rec["repo"],
                "file": rec["file"],
                "category": rec["category"],
                "num_steps": rec["num_steps"],
                "readme": rec["readme"],
                "inputs": [x for x in rec["inputs"] if x],
                "outputs": [y for y in rec["outputs"] if y],
            }
    return out


def fetch_label_embeddings(driver, label: str, id_prop: str) -> List[Tuple[Any, Dict[str, Any], List[float]]]:
    # Return (id, props, embedding)
    q = f"MATCH (n:{label}) WHERE n.embedding IS NOT NULL RETURN n.{id_prop} AS id, n AS n, n.embedding AS e"
    out = []
    with driver.session() as session:
        for rec in session.run(q):
            out.append((rec["id"], dict(rec["n"]), rec["e"]))
    return out


def compute_scores(emb_matrix: np.ndarray, q_vec: np.ndarray) -> np.ndarray:
    # Both are normalized (embed_nodes stored normalized vectors). Cosine = dot.
    return emb_matrix @ q_vec


def main():
    parser = argparse.ArgumentParser(description="Semantic search over nodes by label")
    parser.add_argument("--label", required=True, help="Node label (e.g., Step, Tool, Workflow)")
    parser.add_argument("--q", required=True, help="Query text")
    parser.add_argument("--k", type=int, default=10, help="Top K results")
    parser.add_argument("--uri", default="bolt://localhost:7687")
    parser.add_argument("--user", default="neo4j")
    parser.add_argument("--password", required=True)
    parser.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2")
    args = parser.parse_args()

    id_map = id_prop_by_label()
    if args.label not in id_map:
        raise SystemExit(f"Unknown label {args.label}. Known: {sorted(id_map.keys())}")

    log.info("Loading model: %s", args.model)
    model = SentenceTransformer(args.model)
    model_l = args.model.lower()
    is_e5 = "e5" in model_l
    is_bge = "bge" in model_l

    prefix = "query: " if (is_e5 or is_bge) else ""
    q_text = prefix + args.q
    q_vec = model.encode([q_text], normalize_embeddings=True)[0]

    driver = GraphDatabase.driver(args.uri, auth=(args.user, args.password))
    try:
        rows = fetch_label_embeddings(driver, args.label, id_map[args.label])
        if not rows:
            print("No nodes with embeddings found for label", args.label)
            return

        ids = [r[0] for r in rows]
        props = [r[1] for r in rows]
        mat = np.array([r[2] for r in rows], dtype=np.float32)
        scores = compute_scores(mat, np.asarray(q_vec, dtype=np.float32))

        top_idx = np.argsort(-scores)[: args.k]

        wf_details = fetch_workflow_details(driver, [ids[i] for i in top_idx]) if args.label == "Workflow" else {}

        print(f"Top {args.k} for label {args.label} and query: {args.q}")
        for rank, i in enumerate(top_idx, 1):
            s = float(scores[i])
            p = props[i]
            node_id = ids[i]

            if args.label == "Step":
                title = " | ".join(
                    [str(x) for x in [p.get("name"), p.get("type"), p.get("tool_id"), p.get("tool_version")] if x]
                )
                print(f"{rank:2d}. score={s:.4f} id={node_id} :: {title}")
            elif args.label == "Workflow":
                detail = wf_details.get(node_id, {})
                repo = detail.get("repo") or p.get("workflow_repository")
                file = detail.get("file") or p.get("file_name")
                cat = detail.get("category") or p.get("category")
                steps = detail.get("num_steps") or p.get("number_of_steps")
                inputs = detail.get("inputs") or []
                outputs = detail.get("outputs") or []
                readme = detail.get("readme") or ""
                if readme and len(readme) > 800:
                    readme = readme[:800] + "..."
                print(f"{rank:2d}. score={s:.4f} id={node_id}")
                print(f"    Workflow: {repo}/{file} | Category: {cat} | Steps: {steps}")
                if inputs:
                    print(f"    Inputs: {', '.join(inputs[:20])}")
                if outputs:
                    print(f"    Outputs: {', '.join(outputs[:20])}")
                if readme:
                    print(f"    README: {readme}")
            elif args.label == "Tool":
                title = " | ".join([str(x) for x in [p.get("name"), p.get("version"), p.get("owner")] if x])
                print(f"{rank:2d}. score={s:.4f} id={node_id} :: {title}")
            else:
                title = ", ".join([f"{k}={v}" for k, v in list(p.items())[:5]])
                print(f"{rank:2d}. score={s:.4f} id={node_id} :: {title}")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
