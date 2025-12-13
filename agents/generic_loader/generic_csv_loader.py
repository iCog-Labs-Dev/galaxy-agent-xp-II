"""Generic CSV → Neo4j loader with configurable nodes and relationships.

This loader is schema-configurable so it can ingest workflow CSVs, tools CSVs,
or other future datasets without hard-coding labels/edges.

Default config supports:
- Workflow CSVs produced by `convert_json_to_csv.py`
- Tool CSVs (e.g., tools_used.csv) to attach tools to workflows

Usage (from repo root):
  python agents/generic_loader/generic_csv_loader.py \
    --csv-dir agents/generic_loader/data \
    --uri bolt://localhost:7687 \
    --user neo4j \
    --password YOUR_PASSWORD

You can extend DEFAULT_CONFIG in `schema_models.py` to add/adjust nodes and relationships.
"""

import argparse
import csv
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Any

from neo4j import GraphDatabase

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def md5_id(values: List[Any]) -> str:
    s = "_".join([str(v) for v in values if v is not None])
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def read_csv(path: Path):
    if not path.exists():
        log.warning("Missing CSV %s", path)
        return []
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


from schema_models import DEFAULT_CONFIG, LoaderConfig, NodeSpec, RelationshipSpec  # noqa: E402


def build_id(row: Dict[str, Any], fields: List[str]) -> str:
    vals = [row.get(f) for f in fields]
    return md5_id(vals)


def merge_nodes(driver, nodes_spec: List[NodeSpec], csv_rows_map):
    with driver.session() as session:
        for spec in nodes_spec:
            rows = csv_rows_map.get(spec.file, [])
            if not rows:
                log.info("[nodes] skipping %s (no rows)", spec.name)
                continue
            log.info("[nodes] merging %s (%d rows)", spec.name, len(rows))

            def work(tx, row):
                node_id = build_id(row, spec.id_fields)
                props = {spec.id_property: node_id}
                for pf in spec.prop_fields:
                    # Map category -> name for Category label; otherwise keep as-is
                    if spec.label == "Category" and pf == "category":
                        props["name"] = row.get(pf, "")
                    else:
                        props[pf] = row.get(pf, "")
                tx.run(
                    f"MERGE (n:{spec.label} {{{spec.id_property}: $node_id}}) SET n += $props",
                    node_id=node_id,
                    props=props,
                )

            for row in rows:
                session.execute_write(work, row)


def merge_relationships(driver, rels_spec: List[RelationshipSpec], nodes_spec_map: List[NodeSpec], csv_rows_map):
    # Precompute id_property per node name for match clauses
    id_prop_by_name = {n.name: n.id_property for n in nodes_spec_map}

    with driver.session() as session:
        for spec in rels_spec:
            rows = csv_rows_map.get(spec.file, [])
            if not rows:
                log.info("[rels] skipping %s (no rows)", spec.type)
                continue
            log.info("[rels] merging %s (%d rows)", spec.type, len(rows))

            def work(tx, row):
                from_id = build_id(row, spec.from_id_fields)
                to_id = build_id(row, spec.to_id_fields)
                rel_props = {}
                for pf in spec.prop_fields:
                    rel_props[pf] = row.get(pf, "")
                if spec.set_source_target:
                    rel_props.setdefault("source_type", spec.from_)
                    rel_props.setdefault("target_type", spec.to)

                tx.run(
                    f"""
                    MATCH (a:{spec.from_} {{{id_prop_by_name[spec.from_]}: $from_id}})
                    MATCH (b:{spec.to} {{{id_prop_by_name[spec.to]}: $to_id}})
                    MERGE (a)-[r:{spec.type}]-(b)
                    SET r += $rel_props
                    """,
                    from_id=from_id,
                    to_id=to_id,
                    rel_props=rel_props,
                )

            for row in rows:
                session.execute_write(work, row)


def main():
    parser = argparse.ArgumentParser(description="Generic CSV -> Neo4j loader (config-driven)")
    parser.add_argument("--csv-dir", default=str(Path(__file__).parent / "data"), help="Directory containing CSV outputs")
    parser.add_argument("--uri", default="bolt://localhost:7687")
    parser.add_argument("--user", default="neo4j")
    parser.add_argument("--password", required=True)
    args = parser.parse_args()

    csv_dir = Path(args.csv_dir)
    csv_rows_map = {}
    config = DEFAULT_CONFIG
    for node in config.nodes:
        csv_rows_map[node.file] = read_csv(csv_dir / node.file)
    for rel in config.relationships:
        if rel.file not in csv_rows_map:
            csv_rows_map[rel.file] = read_csv(csv_dir / rel.file)

    driver = GraphDatabase.driver(args.uri, auth=(args.user, args.password))
    try:
        merge_nodes(driver, config.nodes, csv_rows_map)
        merge_relationships(driver, config.relationships, config.nodes, csv_rows_map)
        log.info("✅ Generic CSV load complete")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
