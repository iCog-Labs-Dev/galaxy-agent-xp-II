"""Execute generated Cypher files (nodes then edges) against Neo4j.

This mirrors the file-driven loader style: it reads *.cypher files, splits on
semicolons, and runs each statement in order. Pair it with
`generate_cypher_files.py` outputs.

Usage (from repo root):
  python agents/generic_loader/cypher_batch_loader.py \
    --cypher-dir agents/generic_loader/cypher_out \
    --uri bolt://localhost:7687 \
    --user neo4j \
    --password YOUR_PASSWORD
"""

import argparse
import logging
from pathlib import Path
from typing import List

from neo4j import GraphDatabase

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def split_statements(text: str) -> List[str]:
    # Simple semicolon splitter; assumes statements end with ';'
    parts = text.split(";")
    return [p.strip() for p in parts if p.strip()]


def run_statements(driver, statements: List[str]):
    with driver.session() as session:
        for stmt in statements:
            session.run(stmt).consume()


def main():
    parser = argparse.ArgumentParser(description="Run Cypher batch files (nodes then edges)")
    parser.add_argument("--cypher-dir", default=str(Path(__file__).parent / "cypher_out"))
    parser.add_argument("--uri", default="bolt://localhost:7687")
    parser.add_argument("--user", default="neo4j")
    parser.add_argument("--password", required=True)
    args = parser.parse_args()

    cy_dir = Path(args.cypher_dir)
    nodes_path = cy_dir / "nodes.cypher"
    edges_path = cy_dir / "edges.cypher"

    if not nodes_path.exists() or not edges_path.exists():
        raise SystemExit(f"Expected nodes.cypher and edges.cypher in {cy_dir}")

    nodes_text = nodes_path.read_text(encoding="utf-8")
    edges_text = edges_path.read_text(encoding="utf-8")
    nodes_stmts = split_statements(nodes_text)
    edges_stmts = split_statements(edges_text)

    driver = GraphDatabase.driver(args.uri, auth=(args.user, args.password))
    try:
        log.info("Running %d node statements", len(nodes_stmts))
        run_statements(driver, nodes_stmts)
        log.info("Running %d edge statements", len(edges_stmts))
        run_statements(driver, edges_stmts)
        log.info("✅ Cypher batch load complete")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
