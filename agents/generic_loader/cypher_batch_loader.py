"""Execute generated Cypher files (nodes then edges) against Neo4j.

Reads *.cypher files one statement per line (trimming a trailing semicolon) so
embedded semicolons inside string values do not break parsing. Pair it with
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
import time
from pathlib import Path

from neo4j import GraphDatabase
from tqdm import tqdm

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def iter_statements(path: Path):
    """Yield statements separated by blank lines, trimming trailing semicolons."""
    buffer: list[str] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                buffer.append(line.rstrip())
                continue
            if buffer:
                stmt = "\n".join(buffer).strip()
                if stmt.endswith(";"):
                    stmt = stmt[:-1]
                yield stmt
                buffer = []
        if buffer:
            stmt = "\n".join(buffer).strip()
            if stmt.endswith(";"):
                stmt = stmt[:-1]
            yield stmt


def count_statements(path: Path) -> int:
    return sum(1 for _ in iter_statements(path))


def run_statements(driver, path: Path, label: str):
    total = count_statements(path)
    start = time.perf_counter()
    with driver.session() as session:
        for stmt in tqdm(iter_statements(path), total=total, desc=label, unit="stmt"):
            session.run(stmt).consume()
    log.info("[%s] done in %.2fs", label, time.perf_counter() - start)


def ensure_indexes(driver):
    """Create id indexes to speed up MERGE-heavy batches."""
    index_statements = [
        "CREATE INDEX cat_id IF NOT EXISTS FOR (n:Category) ON (n.category_id)",
        "CREATE INDEX wf_id IF NOT EXISTS FOR (n:Workflow) ON (n.workflow_id)",
        "CREATE INDEX step_id IF NOT EXISTS FOR (n:Step) ON (n.step_uid)",
        "CREATE INDEX tool_id IF NOT EXISTS FOR (n:Tool) ON (n.tool_id)",
        "CREATE INDEX tin_id IF NOT EXISTS FOR (n:ToolInput) ON (n.tool_input_uid)",
        "CREATE INDEX tout_id IF NOT EXISTS FOR (n:ToolOutput) ON (n.tool_output_uid)",
        "CREATE INDEX in_id IF NOT EXISTS FOR (n:Input) ON (n.input_uid)",
        "CREATE INDEX out_id IF NOT EXISTS FOR (n:Output) ON (n.output_uid)",
    ]
    with driver.session() as session:
        for stmt in index_statements:
            session.run(stmt).consume()
    log.info("Indexes ensured")


def main():
    parser = argparse.ArgumentParser(description="Run Cypher batch files (nodes then edges)")
    parser.add_argument("--cypher-dir", default=str(Path(__file__).parent / "cypher_out"))
    parser.add_argument("--uri", default="bolt://localhost:7687")
    parser.add_argument("--user", default="neo4j")
    parser.add_argument("--password", required=True)
    parser.add_argument("--create-indexes", action="store_true", help="Create IF NOT EXISTS indexes for node ids before loading")
    args = parser.parse_args()

    cy_dir = Path(args.cypher_dir)
    nodes_path = cy_dir / "nodes.cypher"
    edges_path = cy_dir / "edges.cypher"

    if not nodes_path.exists() or not edges_path.exists():
        raise SystemExit(f"Expected nodes.cypher and edges.cypher in {cy_dir}")

    driver = GraphDatabase.driver(args.uri, auth=(args.user, args.password))
    try:
        if args.create_indexes:
            ensure_indexes(driver)
        run_statements(driver, nodes_path, "nodes")
        run_statements(driver, edges_path, "edges")
        log.info("✅ Cypher batch load complete")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
