from neo4j import GraphDatabase  # type: ignore

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
            print(f"[neo4j][merge_rel] error merging rel {type} between {from_label} and {to_label}: {e} - neo4j_client.py:134")
            raise
