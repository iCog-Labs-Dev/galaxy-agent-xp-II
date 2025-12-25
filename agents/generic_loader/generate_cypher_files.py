import argparse
import csv
import hashlib
from pathlib import Path
from typing import Any, Dict, List

from schema_models import DEFAULT_CONFIG, NodeSpec, RelationshipSpec


def md5_id(values: List[Any]) -> str:
    s = "_".join([str(v) for v in values if v is not None])
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def escape(val: Any) -> str:
    """Escape a value for Cypher string literal; store everything as string for parity."""
    if val is None:
        val = ""
    return str(val).replace("\\", "\\\\").replace("'", "\\'")


def read_csv(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def build_id(row: Dict[str, Any], fields: List[str]) -> str:
    vals = [row.get(f) for f in fields]
    return md5_id(vals)


def node_statements(config_nodes: List[NodeSpec], csv_dir: Path, csv_rows_map):
    stmts = []
    for spec in config_nodes:
        rows = csv_rows_map.get(spec.file, [])
        for row in rows:
            node_id = build_id(row, spec.id_fields)
            props: Dict[str, Any] = {spec.id_property: node_id}
            for pf in spec.prop_fields:
                if spec.label == "Category" and pf == "category":
                    props.setdefault("name", row.get(pf, ""))
                props[pf] = row.get(pf, "")
            props_literal = ", ".join([f"`{k}`: '{escape(v)}'" for k, v in props.items()])
            stmts.append(
                f"MERGE (n:{spec.label} {{{spec.id_property}: '{node_id}'}}) SET n += {{{props_literal}}};"
            )
    return stmts


def rel_statements(config_rels: List[RelationshipSpec], config_nodes: List[NodeSpec], csv_rows_map):
    stmts = []
    id_prop_by_name = {n.name: n.id_property for n in config_nodes}
    for spec in config_rels:
        rows = csv_rows_map.get(spec.file, [])
        for row in rows:
            from_id = build_id(row, spec.from_id_fields)
            to_id = build_id(row, spec.to_id_fields)
            rel_props: Dict[str, Any] = {}
            for pf in spec.prop_fields:
                rel_props[pf] = row.get(pf, "")
            if spec.set_source_target:
                rel_props.setdefault("source_type", spec.from_)
                rel_props.setdefault("target_type", spec.to)
            props_literal = ", ".join([f"`{k}`: '{escape(v)}'" for k, v in rel_props.items()])
            if props_literal:
                props_clause = f" SET r += {{{props_literal}}}"
            else:
                props_clause = ""
            stmts.append(
                f"MATCH (a:{spec.from_} {{{id_prop_by_name[spec.from_]}: '{from_id}'}}) "
                f"MATCH (b:{spec.to} {{{id_prop_by_name[spec.to]}: '{to_id}'}}) "
                f"MERGE (a)-[r:{spec.type}]-(b){props_clause};"
            )
    return stmts


def write_file(path: Path, statements: List[str]):
    if not statements:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        f.write("\n".join(statements))
    print(f"Wrote {len(statements)} statements to {path}")


def main():
    parser = argparse.ArgumentParser(description="Generate Cypher files for nodes and edges from CSVs")
    parser.add_argument("--csv-dir", default=str(Path(__file__).parent / "data"), help="Directory with CSV inputs")
    parser.add_argument("--out-dir", default=str(Path(__file__).parent / "cypher_out"), help="Directory to write Cypher files")
    args = parser.parse_args()

    csv_dir = Path(args.csv_dir)
    out_dir = Path(args.out_dir)

    config = DEFAULT_CONFIG
    csv_rows_map = {}
    for node in config.nodes:
        csv_rows_map[node.file] = read_csv(csv_dir / node.file)
    for rel in config.relationships:
        if rel.file not in csv_rows_map:
            csv_rows_map[rel.file] = read_csv(csv_dir / rel.file)

    nodes_cypher = node_statements(config.nodes, csv_dir, csv_rows_map)
    edges_cypher = rel_statements(config.relationships, config.nodes, csv_rows_map)

    write_file(out_dir / "nodes.cypher", nodes_cypher)
    write_file(out_dir / "edges.cypher", edges_cypher)


if __name__ == "__main__":
    main()
