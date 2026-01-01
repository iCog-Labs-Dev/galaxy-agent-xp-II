import argparse
import csv
import hashlib
import logging
import math
import time
from itertools import islice
from pathlib import Path
from typing import Any, Dict, List

from neo4j import GraphDatabase
from tqdm import tqdm

BATCH_SIZE_DEFAULT = 2000

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def md5_id(values: List[Any]) -> str:
    s = "_".join([str(v) for v in values if v is not None])
    return hashlib.md5(s.encode("utf-8")).hexdigest()


from schema_models import DEFAULT_CONFIG, LoaderConfig, NodeSpec, RelationshipSpec


def build_id(row: Dict[str, Any], fields: List[str]) -> str:
    vals = [row.get(f) for f in fields]
    return md5_id(vals)


def count_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8") as f:
        # subtract header if present
        line_count = sum(1 for _ in f)
    return max(0, line_count - 1)


def iter_csv_batches(path: Path, size: int):
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        while True:
            chunk = list(islice(reader, size))
            if not chunk:
                return
            yield chunk


def merge_nodes(driver, nodes_spec: List[NodeSpec], csv_dir: Path, batch_size: int):
    with driver.session() as session:
        for spec in nodes_spec:
            path = csv_dir / spec.file
            row_count = count_rows(path)
            if row_count == 0:
                log.info("[nodes] skipping %s (no rows)", spec.name)
                continue
            log.info("[nodes] merging %s (%d rows)", spec.name, row_count)
            start = time.perf_counter()

            cypher = (
                f"UNWIND $rows AS row "
                f"MERGE (n:{spec.label} {{{spec.id_property}: row.node_id}}) "
                f"SET n += row.props"
            )

            total_batches = math.ceil(row_count / batch_size) if row_count else None
            for chunk in tqdm(
                iter_csv_batches(path, batch_size),
                desc=f"nodes:{spec.name}",
                unit="batch",
                total=total_batches,
                leave=False,
            ):
                payload = []
                for row in chunk:
                    node_id = build_id(row, spec.id_fields)
                    props = {spec.id_property: node_id}
                    for pf in spec.prop_fields:
                        if spec.label == "Category" and pf == "category":
                            props["name"] = row.get(pf, "")
                        else:
                            props[pf] = row.get(pf, "")
                    payload.append({"node_id": node_id, "props": props})
                session.execute_write(lambda tx, c=payload: tx.run(cypher, rows=c))
            log.info("[nodes] %s done in %.2fs", spec.name, time.perf_counter() - start)


def merge_relationships(driver, rels_spec: List[RelationshipSpec], nodes_spec_map: List[NodeSpec], csv_dir: Path, batch_size: int):
    # Precompute id_property per node name for match clauses
    id_prop_by_name = {n.name: n.id_property for n in nodes_spec_map}

    with driver.session() as session:
        for spec in rels_spec:
            path = csv_dir / spec.file
            row_count = count_rows(path)
            if row_count == 0:
                log.info("[rels] skipping %s (no rows)", spec.type)
                continue
            log.info("[rels] merging %s (%d rows)", spec.type, row_count)
            start = time.perf_counter()

            cypher = (
                f"UNWIND $rows AS row "
                f"MATCH (a:{spec.from_} {{{id_prop_by_name[spec.from_]}: row.from_id}}) "
                f"MATCH (b:{spec.to} {{{id_prop_by_name[spec.to]}: row.to_id}}) "
                f"MERGE (a)-[r:{spec.type}]-(b) "
                f"SET r += row.props"
            )

            total_batches = math.ceil(row_count / batch_size) if row_count else None
            for chunk in tqdm(
                iter_csv_batches(path, batch_size),
                desc=f"rels:{spec.type}",
                unit="batch",
                total=total_batches,
                leave=False,
            ):
                payload = []
                for row in chunk:
                    from_id = build_id(row, spec.from_id_fields)
                    to_id = build_id(row, spec.to_id_fields)
                    rel_props = {}
                    for pf in spec.prop_fields:
                        rel_props[pf] = row.get(pf, "")
                    if spec.set_source_target:
                        rel_props.setdefault("source_type", spec.from_)
                        rel_props.setdefault("target_type", spec.to)
                    payload.append({
                        "from_id": from_id,
                        "to_id": to_id,
                        "props": rel_props,
                    })
                session.execute_write(lambda tx, c=payload: tx.run(cypher, rows=c))
            log.info("[rels] %s done in %.2fs", spec.type, time.perf_counter() - start)


def main():
    parser = argparse.ArgumentParser(description="Generic CSV -> Neo4j loader (config-driven)")
    parser.add_argument("--csv-dir", default=str(Path(__file__).parent / "data"), help="Directory containing CSV outputs")
    parser.add_argument("--uri", default="bolt://localhost:7687")
    parser.add_argument("--user", default="neo4j")
    parser.add_argument("--password", required=True)
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE_DEFAULT, help="Rows per UNWIND batch (default 2000)")
    args = parser.parse_args()

    csv_dir = Path(args.csv_dir)
    config = DEFAULT_CONFIG

    driver = GraphDatabase.driver(args.uri, auth=(args.user, args.password))
    try:
        merge_nodes(driver, config.nodes, csv_dir, args.batch_size)
        merge_relationships(driver, config.relationships, config.nodes, csv_dir, args.batch_size)
        log.info("✅ Generic CSV load complete")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
