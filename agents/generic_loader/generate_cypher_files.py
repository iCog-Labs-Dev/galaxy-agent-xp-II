import argparse
from pathlib import Path
from typing import List

from schema_models import DEFAULT_CONFIG, NodeSpec, RelationshipSpec


def build_md5_expression(source_alias: str, fields: List[str]) -> str:
    # apoc.util.md5 expects a list; passing a string causes "expected List but was String"
    joined_fields = ", ".join([f"coalesce({source_alias}.`{f}`, '')" for f in fields])
    return f"apoc.util.md5([{joined_fields}])"


def _humanize_key(key: str) -> str:
    return key.replace("_", " ").title()


def build_content_expression(content_fields: List[tuple[str, str]]) -> str:
    parts = []
    for key, value_expr in content_fields:
        label = _humanize_key(key)
        parts.append(
            f"CASE WHEN coalesce({value_expr}, '') <> '' "
            f"THEN 'The {label} is ' + toString({value_expr}) + '. ' ELSE '' END"
        )
    if not parts:
        return "''"
    return " + ".join(parts)


def node_statement(spec: NodeSpec, csv_url: str, batch_size: int, parallel: bool, concurrency: int) -> str:
    id_expr = build_md5_expression("row", spec.id_fields)
    props_entries = [f"`{spec.id_property}`: node_id"]
    content_fields: List[tuple[str, str]] = [(spec.id_property, "node_id")]
    for pf in spec.prop_fields:
        if spec.label == "Category" and pf == "category":
            props_entries.append("`name`: coalesce(row.`category`, '')")
            content_fields.append(("name", "coalesce(row.`category`, '')"))
        props_entries.append(f"`{pf}`: coalesce(row.`{pf}`, '')")
        content_fields.append((pf, f"coalesce(row.`{pf}`, '')"))

    content_expr = build_content_expression(content_fields)
    props_entries.append(f"`content`: trim({content_expr})")
    props_literal = ", ".join(props_entries)
    action_lines = [
        f"WITH row, {id_expr} AS node_id",
        f"MERGE (n:{spec.label} {{{spec.id_property}: node_id}})",
        f"SET n += {{{props_literal}}}",
    ]
    action_query = "\\n".join(action_lines)
    return (
        "CALL apoc.periodic.iterate(\n"
        f"  \"LOAD CSV WITH HEADERS FROM '{csv_url}' AS row RETURN row\",\n"
        f"  \"{action_query}\",\n"
        f"  {{batchSize:{batch_size}, parallel:{str(parallel).lower()}, concurrency:{concurrency}}}\n"
        ");"
    )


def rel_statement(
    spec: RelationshipSpec,
    csv_url: str,
    batch_size: int,
    parallel: bool,
    concurrency: int,
    id_prop_by_name: dict,
) -> str:
    from_expr = build_md5_expression("row", spec.from_id_fields)
    to_expr = build_md5_expression("row", spec.to_id_fields)
    props_entries = []
    for pf in spec.prop_fields:
        props_entries.append(f"`{pf}`: coalesce(row.`{pf}`, '')")
    props_literal = ", ".join(props_entries)
    props_clause = f"SET r += {{{props_literal}}}" if props_literal else ""
    if spec.type == "STEP_USES_WORKFLOW":
        action_lines = [
            f"WITH row, {from_expr} AS from_id",
            f"MATCH (a:{spec.from_} {{{id_prop_by_name[spec.from_]}: from_id}})",
            f"MATCH (b:{spec.to} {{workflow_repository: coalesce(row.`workflow_repository`, ''), workflow_name: coalesce(row.`subworkflow_name`, '')}})",
            "WHERE coalesce(row.`subworkflow_name`, '') <> ''",
            f"MERGE (a)-[r:{spec.type}]->(b)",
        ]
    else:
        action_lines = [
            f"WITH row, {from_expr} AS from_id, {to_expr} AS to_id",
            f"MATCH (a:{spec.from_} {{{id_prop_by_name[spec.from_]}: from_id}})",
            f"MATCH (b:{spec.to} {{{id_prop_by_name[spec.to]}: to_id}})",
            f"MERGE (a)-[r:{spec.type}]->(b)",
        ]
    if props_clause:
        action_lines.append(props_clause)
    if spec.set_source_target:
        action_lines.extend([
            f"SET r.source_type = coalesce(r.source_type, '{spec.from_}')",
            f"SET r.target_type = coalesce(r.target_type, '{spec.to}')",
        ])
    action_query = "\\n".join(action_lines)
    return (
        "CALL apoc.periodic.iterate(\n"
        f"  \"LOAD CSV WITH HEADERS FROM '{csv_url}' AS row RETURN row\",\n"
        f"  \"{action_query}\",\n"
        f"  {{batchSize:{batch_size}, parallel:{str(parallel).lower()}, concurrency:{concurrency}}}\n"
        ");"
    )


def build_csv_url(csv_dir: Path, filename: str, prefix: str | None, absolute: bool) -> str:
    if absolute:
        return (csv_dir / filename).resolve().as_uri()
    if prefix:
        base = prefix[:-1] if prefix.endswith("/") else prefix
        return f"{base}/{filename}"
    resolved = csv_dir.resolve().as_posix().rstrip("/")
    return f"file://{resolved}/{filename}"


def write_file(path: Path, statements: List[str]):
    if not statements:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        f.write("\n\n".join(statements))
    print(f"Wrote {len(statements)} statements to {path}")


def main():
    parser = argparse.ArgumentParser(description="Generate APOC Cypher files for nodes and edges from CSVs")
    parser.add_argument("--csv-dir", default=str(Path(__file__).parent / "data"), help="Directory with CSV inputs")
    parser.add_argument("--out-dir", default=str(Path(__file__).parent / "cypher_out"), help="Directory to write Cypher files")
    parser.add_argument("--csv-uri-prefix", help="Override LOAD CSV prefix, e.g. file:///neo4j/import")
    parser.add_argument("--batch-size", type=int, default=2000)
    parser.add_argument("--parallel", action="store_true", help="Use APOC parallel batches")
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--csv-absolute-paths", action="store_true", help="Embed absolute file:/// paths (requires allow_csv_import_from_file_urls=true)")
    args = parser.parse_args()

    csv_dir = Path(args.csv_dir)
    out_dir = Path(args.out_dir)

    config = DEFAULT_CONFIG
    nodes_statements: List[str] = []
    for spec in config.nodes:
        csv_path = csv_dir / spec.file
        if not csv_path.exists():
            continue
        csv_url = build_csv_url(csv_dir, spec.file, args.csv_uri_prefix, args.csv_absolute_paths)
        nodes_statements.append(
            node_statement(spec, csv_url, args.batch_size, args.parallel, args.concurrency)
        )

    id_prop_by_name = {n.name: n.id_property for n in config.nodes}
    rel_statements_list: List[str] = []
    for spec in config.relationships:
        csv_path = csv_dir / spec.file
        if not csv_path.exists():
            continue
        csv_url = build_csv_url(csv_dir, spec.file, args.csv_uri_prefix, args.csv_absolute_paths)
        rel_statements_list.append(
            rel_statement(
                spec,
                csv_url,
                args.batch_size,
                args.parallel,
                args.concurrency,
                id_prop_by_name,
            )
        )

    write_file(out_dir / "nodes.cypher", nodes_statements)
    write_file(out_dir / "edges.cypher", rel_statements_list)


if __name__ == "__main__":
    main()
