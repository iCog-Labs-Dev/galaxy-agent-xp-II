"""Compute and store text embeddings on graph nodes for semantic search.

Uses a free, widely adopted open model: sentence-transformers/all-MiniLM-L6-v2
(384-dim, cosine-friendly). You can switch models via --model.

Embeddings are stored on each node as a float list property `embedding`.
Optionally attempts to create per-label vector indexes if supported by your
Neo4j version.

Usage (from repo root):
  python agents/generic_loader/embed_nodes.py \
    --uri bolt://localhost:7687 \
    --user neo4j \
    --password YOUR_PASSWORD \
    --labels Workflow Step Tool Input Output Category \
    --model sentence-transformers/all-MiniLM-L6-v2 \
    --create-index
"""

import argparse
import logging
from typing import Dict, Any, List, Tuple

from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer

from schema_models import DEFAULT_CONFIG, NodeSpec

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def id_prop_by_label() -> Dict[str, str]:
    return {spec.label: spec.id_property for spec in DEFAULT_CONFIG.nodes}


def build_text(label: str, props: Dict[str, Any]) -> str:
    # Heuristics per label to form a meaningful description for embedding
    if label == "Workflow":
        return " ".join(filter(None, [props.get("workflow_repository"), props.get("file_name"), props.get("category")]))
    if label == "Step":
        return " ".join(filter(None, [props.get("name"), props.get("type"), props.get("annotation"), props.get("tool_id"), props.get("tool_version")]))
    if label == "Input":
        return " ".join(filter(None, [props.get("name"), props.get("description")]))
    if label == "Output":
        return " ".join(filter(None, [props.get("name"), props.get("description")]))
    if label == "Tool":
        return " ".join(filter(None, [props.get("name"), props.get("version"), props.get("owner"), props.get("tool_category"), props.get("tool_shed_url")]))
    if label == "Category":
        return props.get("name") or props.get("category") or ""
    # Fallback: join all string-like props
    parts = []
    for k, v in props.items():
        if isinstance(v, (str, int, float)):
            parts.append(str(v))
    return " ".join(parts)


def fetch_nodes(driver, label: str, id_prop: str) -> List[Dict[str, Any]]:
    q = f"MATCH (n:{label}) RETURN n, n.{id_prop} AS id"
    rows: List[Dict[str, Any]] = []
    with driver.session() as session:
        for rec in session.run(q):
            node = rec["n"]
            props = dict(node)
            rows.append({"id": rec["id"], "props": props})
    return rows


def set_embedding(driver, label: str, id_prop: str, node_id: Any, vec: List[float]):
    with driver.session() as session:
        session.run(
            f"MATCH (n:{label} {{{id_prop}: $id}}) SET n.embedding = $vec",
            id=node_id,
            vec=vec,
        ).consume()


def try_create_vector_index(driver, label: str, id_prop: str, dim: int):
    # Neo4j native vector index (Neo4j 5.15+). Guarded with try/except for older versions.
    cy = (
        f"CREATE VECTOR INDEX IF NOT EXISTS {label.lower()}_embedding_index "
        f"FOR (n:{label}) ON (n.embedding) "
        f"OPTIONS {{ indexConfig: {{ 'vector.dimensions': {dim}, 'vector.similarityFunction': 'cosine' }} }}"
    )
    try:
        with driver.session() as session:
            session.run(cy).consume()
        log.info("Vector index ensured for label %s", label)
    except Exception as e:
        log.info("Vector index not created for %s (likely unsupported Neo4j version): %s", label, e)


def load_workflow_readmes(csv_dir: str) -> Dict[str, str]:
    """Map workflow_repository -> readme_content (if available)."""
    import csv
    from pathlib import Path

    path = Path(csv_dir) / "workflows.csv"
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    out: Dict[str, str] = {}
    for r in rows:
        repo = r.get("workflow_repository") or r.get("repository") or ""
        readme = r.get("readme_content") or ""
        if repo:
            out[repo] = readme
    return out


def fetch_workflow_summaries(driver) -> Dict[str, Tuple[int, List[str], List[str]]]:
    """Return map of workflow_id -> (steps_count, inputs[], outputs[])."""
    q = (
        "MATCH (w:Workflow)\n"
        "OPTIONAL MATCH (w)-[:HAS_STEP]->(s:Step)\n"
        "OPTIONAL MATCH (s)-[:STEP_REQUIRES]->(i:Input)\n"
        "OPTIONAL MATCH (s)-[:STEP_GENERATES]->(o:Output)\n"
        "RETURN w.workflow_id AS id, count(DISTINCT s) AS steps, "
        "collect(DISTINCT i.name) AS inputs, collect(DISTINCT o.name) AS outputs"
    )
    out: Dict[str, Tuple[int, List[str], List[str]]] = {}
    with driver.session() as session:
        for rec in session.run(q):
            out[rec["id"]] = (rec["steps"], [x for x in rec["inputs"] if x], [y for y in rec["outputs"] if y])
    return out


def build_workflow_text(props: Dict[str, Any], summary: Tuple[int, List[str], List[str]] | None, readme: str | None) -> str:
    repo = props.get("workflow_repository") or ""
    fname = props.get("file_name") or ""
    cat = props.get("category") or ""
    steps_prop = props.get("number_of_steps")
    steps_count = summary[0] if summary else steps_prop or 0
    inputs = summary[1] if summary else []
    outputs = summary[2] if summary else []
    # limit IO lists to avoid very long texts
    inputs_s = ", ".join(inputs[:50])
    outputs_s = ", ".join(outputs[:50])
    # trim README to a reasonable size
    readme = (readme or "").strip()
    if len(readme) > 4000:
        readme = readme[:4000]
    parts = [
        f"Workflow: {repo}/{fname}",
        f"Category: {cat}",
        f"Steps: {steps_count}",
        f"Inputs: [{inputs_s}]",
        f"Outputs: [{outputs_s}]",
        f"README: {readme}",
    ]
    return "\n".join(parts)


def fetch_step_contexts(driver) -> Dict[str, Dict[str, Any]]:
    """Map step_uid -> {repo, file_name, inputs, outputs}."""
    q = (
        "MATCH (w:Workflow)-[:HAS_STEP]->(s:Step)\n"
        "OPTIONAL MATCH (s)-[:STEP_REQUIRES]->(i:Input)\n"
        "OPTIONAL MATCH (s)-[:STEP_GENERATES]->(o:Output)\n"
        "RETURN s.step_uid AS sid, w.workflow_repository AS repo, w.file_name AS file, "
        "collect(DISTINCT i.name) AS inputs, collect(DISTINCT o.name) AS outputs"
    )
    out: Dict[str, Dict[str, Any]] = {}
    with driver.session() as session:
        for rec in session.run(q):
            out[rec["sid"]] = {
                "repo": rec["repo"],
                "file": rec["file"],
                "inputs": [x for x in rec["inputs"] if x],
                "outputs": [y for y in rec["outputs"] if y],
            }
    return out


def build_step_text(props: Dict[str, Any], ctx: Dict[str, Any] | None, readmes: Dict[str, str]) -> str:
    name = props.get("name") or ""
    typ = props.get("type") or ""
    annot = props.get("annotation") or ""
    tool_id = props.get("tool_id") or ""
    tool_ver = props.get("tool_version") or ""
    repo = ctx.get("repo") if ctx else ""
    file_name = ctx.get("file") if ctx else ""
    inputs = ctx.get("inputs") if ctx else []
    outputs = ctx.get("outputs") if ctx else []
    readme = readmes.get(repo or "") or ""
    if len(readme) > 1000:
        readme = readme[:1000]
    inputs_s = ", ".join(inputs[:30])
    outputs_s = ", ".join(outputs[:30])
    parts = [
        f"Step: {name}",
        f"Type: {typ}",
        f"Tool: {tool_id} {tool_ver}".strip(),
        f"Workflow: {repo}/{file_name}",
        f"Inputs: [{inputs_s}]",
        f"Outputs: [{outputs_s}]",
        f"Notes: {annot}",
        f"Workflow README: {readme}",
    ]
    return "\n".join([p for p in parts if p and p.strip()])


def main():
    parser = argparse.ArgumentParser(description="Compute/store node embeddings for semantic search")
    parser.add_argument("--uri", default="bolt://localhost:7687")
    parser.add_argument("--user", default="neo4j")
    parser.add_argument("--password", required=True)
    parser.add_argument(
        "--labels",
        nargs="+",
        default=[spec.label for spec in DEFAULT_CONFIG.nodes],
        help="Node labels to embed",
    )
    parser.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2", help="SentenceTransformer model id")
    parser.add_argument("--csv-dir", default=str("agents/generic_loader/data"), help="CSV dir to enrich workflows (for README)")
    parser.add_argument("--create-index", action="store_true", help="Attempt to create vector indexes per label")
    args = parser.parse_args()

    log.info("Loading embedding model: %s", args.model)
    model = SentenceTransformer(args.model)
    is_e5 = "e5" in args.model.lower()
    dim = model.get_sentence_embedding_dimension()
    id_map = id_prop_by_label()

    driver = GraphDatabase.driver(args.uri, auth=(args.user, args.password))
    try:
        # Pre-enrichment for workflows
        enrich_wf = "Workflow" in args.labels or "Step" in args.labels
        readmes = load_workflow_readmes(args.csv_dir) if enrich_wf else {}
        wf_summaries = fetch_workflow_summaries(driver) if "Workflow" in args.labels else {}
        step_ctx = fetch_step_contexts(driver) if "Step" in args.labels else {}

        for label in args.labels:
            id_prop = id_map.get(label)
            if not id_prop:
                log.warning("Skipping label %s (no id property in config)", label)
                continue
            log.info("Embedding label %s (id prop: %s)", label, id_prop)
            rows = fetch_nodes(driver, label, id_prop)
            if not rows:
                log.info("No nodes found for %s", label)
                continue

            if label == "Workflow":
                texts = []
                for r in rows:
                    props = r["props"]
                    wid = r["id"]
                    summary = wf_summaries.get(wid)
                    readme = readmes.get(props.get("workflow_repository") or "")
                    texts.append(build_workflow_text(props, summary, readme))
                if is_e5:
                    texts = ["passage: " + t for t in texts]
            elif label == "Step":
                texts = []
                for r in rows:
                    props = r["props"]
                    sid = r["id"]
                    ctx = step_ctx.get(sid)
                    texts.append(build_step_text(props, ctx, readmes))
                if is_e5:
                    texts = ["passage: " + t for t in texts]
            else:
                texts = [build_text(label, r["props"]) for r in rows]
                if is_e5:
                    texts = ["passage: " + t for t in texts]
            # Replace empty texts with id to avoid zero vectors
            texts = [t if t and t.strip() else str(r["id"]) for t, r in zip(texts, rows)]

            embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
            for r, vec in zip(rows, embeddings):
                set_embedding(driver, label, id_prop, r["id"], vec.tolist())
            log.info("Stored embeddings for %d %s nodes", len(rows), label)

            if args.create_index:
                try_create_vector_index(driver, label, id_prop, dim)
    finally:
        driver.close()


if __name__ == "__main__":
    main()
