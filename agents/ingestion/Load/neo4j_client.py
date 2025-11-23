from neo4j import GraphDatabase  # type: ignore

class Neo4jClient:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def merge_node(self, label, properties):
        props = ", ".join([f"{k}: ${k}" for k in properties.keys()])
        query = f"MERGE (n:{label} {{ {props} }}) RETURN id(n)"
        with self.driver.session() as s:
            s.run(query, **properties)

    def merge_rel(self, type, from_label, from_props, to_label, to_props, rel_props):
        fp = ", ".join([f"{k}: $fp_{k}" for k in from_props.keys()])
        tp = ", ".join([f"{k}: $tp_{k}" for k in to_props.keys()])
        rp = ", ".join([f"{k}: $rp_{k}" for k in rel_props.keys()]) if rel_props else ""

        query = f"""
        MATCH (a:{from_label} {{ {fp} }})
        MATCH (b:{to_label} {{ {tp} }})
        MERGE (a)-[r:{type} {{ {rp} }}]->(b)
        """

        params = {f"fp_{k}": v for k, v in from_props.items()}
        params.update({f"tp_{k}": v for k, v in to_props.items()})
        params.update({f"rp_{k}": v for k, v in rel_props.items()})

        with self.driver.session() as s:
            s.run(query, **params)
