from neo4j import GraphDatabase  # type: ignore

class Neo4jClient:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def create_indexes(self) -> None:
        """Create helpful indexes for commonly-queried unique keys.

        Creates indexes for:
        - Tool.tool_id
        - ToolCategory.category_id
        - ToolInput.input_uid
        - ToolOutput.output_uid

        This method issues `CREATE INDEX IF NOT EXISTS` statements and is
        idempotent.
        """
        queries = [
            "CREATE INDEX IF NOT EXISTS FOR (t:Tool) ON (t.tool_id)",
            "CREATE INDEX IF NOT EXISTS FOR (c:ToolCategory) ON (c.category_id)",
            "CREATE INDEX IF NOT EXISTS FOR (i:ToolInput) ON (i.input_uid)",
            "CREATE INDEX IF NOT EXISTS FOR (o:ToolOutput) ON (o.output_uid)",
            "CREATE INDEX IF NOT EXISTS FOR (w:Workflow) ON (w.workflow_id)",
            "CREATE INDEX IF NOT EXISTS FOR (s:Step) ON (s.step_uid)",
        ]

        try:
            with self.driver.session() as s:
                for q in queries:
                    s.run(q)
        except Exception as e:
            print(f"[neo4j][create_indexes] error creating indexes: {e}")
            raise

    def merge_node(self, label, properties, unique_key=None):
        """
        Merge a node using only its unique key, update other properties.
        """
        if unique_key is None:
            raise ValueError("unique_key must be specified for MERGE")
        # Ensure unique key exists and is not None
        if unique_key not in properties or properties[unique_key] is None:
            raise ValueError(f"unique_key '{unique_key}' missing or None in properties: {properties}")

        # Use only non-None properties for SET to avoid matching on nulls
        merge_value = properties[unique_key]
        set_props = {k: v for k, v in properties.items() if k != unique_key and v is not None}

        merge_str = f"{unique_key}: ${unique_key}"

        if set_props:
            set_str = ", ".join([f"n.{k} = ${k}" for k in set_props.keys()])
            query = f"""
            MERGE (n:{label} {{ {merge_str} }})
            SET {set_str}
            RETURN elementId(n)
            """
        else:
            # No additional properties to set
            query = f"""
            MERGE (n:{label} {{ {merge_str} }})
            RETURN elementId(n)
            """

        params = {unique_key: merge_value}
        params.update(set_props)

        try:
            with self.driver.session() as s:
                s.run(query, **params)
        except Exception as e:
            print(f"[neo4j][merge_node] error merging node {label} on {unique_key}={merge_value}: {e}")
            raise

    def merge_rel(self, type, from_label, from_props, to_label, to_props, rel_props):
        # Filter out None-valued properties to avoid MATCH on nulls
        fp_dict = {k: v for k, v in from_props.items() if v is not None}
        tp_dict = {k: v for k, v in to_props.items() if v is not None}
        rp_dict = {k: v for k, v in (rel_props or {}).items() if v is not None}

        if not fp_dict:
            raise ValueError(f"No non-null properties to match for from node {from_label}: {from_props}")
        if not tp_dict:
            raise ValueError(f"No non-null properties to match for to node {to_label}: {to_props}")

        fp = ", ".join([f"{k}: $fp_{k}" for k in fp_dict.keys()])
        tp = ", ".join([f"{k}: $tp_{k}" for k in tp_dict.keys()])

        if rp_dict:
            rp = ", ".join([f"{k}: $rp_{k}" for k in rp_dict.keys()])
            rel_clause = f"{{ {rp} }}"
        else:
            rel_clause = ""

        query = f"""
        MATCH (a:{from_label} {{ {fp} }})
        MATCH (b:{to_label} {{ {tp} }})
        MERGE (a)-[r:{type} {rel_clause}]->(b)
        """

        params = {f"fp_{k}": v for k, v in fp_dict.items()}
        params.update({f"tp_{k}": v for k, v in tp_dict.items()})
        params.update({f"rp_{k}": v for k, v in rp_dict.items()})

        try:
            with self.driver.session() as s:
                s.run(query, **params)
        except Exception as e:
            print(f"[neo4j][merge_rel] error merging rel {type} between {from_label} and {to_label}: {e}")
            raise
