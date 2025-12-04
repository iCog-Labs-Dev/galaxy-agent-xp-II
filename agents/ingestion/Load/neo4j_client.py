import time
from functools import wraps
from neo4j import GraphDatabase  # type: ignore
from neo4j.exceptions import SessionExpired, TransientError

def retry(max_retries=3, backoff=1.0):
    """
    Decorator to retry Neo4j queries on SessionExpired or TransientError.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            while attempt < max_retries:
                try:
                    return func(*args, **kwargs)
                except (SessionExpired, TransientError) as e:
                    wait = backoff * (2 ** attempt)
                    print(f"[neo4j][retry] attempt {attempt+1}/{max_retries} after {wait}s due to: {e} - neo4j_client.py:19")
                    time.sleep(wait)
                    attempt += 1
            # Final attempt without catching exception
            return func(*args, **kwargs)
        return wrapper
    return decorator


class Neo4jClient:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def _generate_id(self, *args):
        import hashlib
        s = "_".join([str(a) for a in args if a is not None])
        return hashlib.md5(s.encode("utf-8")).hexdigest()

    def get_unique_key_value(self, schema, properties):
        unique_fields = schema.get("unique_key", [])

        if not unique_fields:
            # no fields specified → generate ID from all properties
            # return self._generate_id(*properties.values())
            return ValueError("No unique_key fields specified in schema")

        # Otherwise, generate ID from listed fields
        values = [properties.get(f) for f in unique_fields]
        return self._generate_id(*values)

    def close(self):
        self.driver.close()

    @retry(max_retries=5, backoff=2.0)
    def merge_node_2(self, node):
        """
        node: output of build_node()
        """
        label = node["label"]
        properties = node["properties"]

        merge_key = "id"
        merge_value = properties[merge_key]

        set_props = {k: v for k, v in properties.items() if k != "id"}

        merge_clause = f"id: $id"

        if set_props:
            set_clause = ", ".join([f"n.{k} = ${k}" for k in set_props])
            query = f"""
            MERGE (n:{label} {{ {merge_clause} }})
            SET {set_clause}
            RETURN elementId(n)
            """
        else:
            query = f"""
            MERGE (n:{label} {{ {merge_clause} }})
            RETURN elementId(n)
            """

        params = {"id": merge_value}
        params.update(set_props)

        with self.driver.session() as s:
            return s.run(query, **params).single().value()


    @retry(max_retries=5, backoff=2.0)
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
            print(f"[neo4j][merge_rel] error merging rel {type} between {from_label} and {to_label}: {e} - neo4j_client.py:122")
            raise
        
    @retry(max_retries=5, backoff=2.0)
    def merge_nodes_batch(self, nodes):
        """
        nodes: list of node dicts from GenericNodeBuilder
        """
        if not nodes:
            return

        query = """
        UNWIND $batch AS n
        MERGE (node:{label} {{ id: n.properties.id }})
        SET node += n.properties
        RETURN count(node)
        """

        # Group nodes by label for efficient batch MERGE
        from collections import defaultdict
        label_groups = defaultdict(list)
        for node in nodes:
            label_groups[node["label"]].append(node)

        with self.driver.session() as s:
            for label, group in label_groups.items():
                params = {"batch": group, "label": label}
                s.run(query.format(label=label), **params)

    @retry(max_retries=5, backoff=2.0)
    def merge_rels_batch(self, rels):
        """
        Accepts a list of relationship Pydantic models.
        Converts them to MERGE queries and pushes to Neo4j.
        """
        for rel in rels:
            print(rel)
            # Extract labels and properties
            rel_label = rel.label
            src_node = rel.source
            tgt_node = rel.target
            rel_props = getattr(rel, "properties", None)

            # Ensure IDs exist
            src_id = src_node["properties"]["id"]
            tgt_id = tgt_node["properties"]["id"]

            # Build relationship MERGE query
            props_clause = ""
            params = {"src_id": src_id, "tgt_id": tgt_id}
            if rel_props is not None:
                props_dict = rel_props.model_dump()  # e.g., OutputInputProperties
                props_clause = " {" + ", ".join([f"{k}: ${k}" for k in props_dict.keys()]) + "}"
                params.update(props_dict)

            query = f"""
            MATCH (a {{id: $src_id}})
            MATCH (b {{id: $tgt_id}})
            MERGE (a)-[r:{rel_label}{props_clause}]->(b)
            """

            # Execute
            with self.neo.driver.session() as s:
                s.run(query, **params)
