# agents/ingestion/Load/neo4j_client.py
import yaml
from neo4j import GraphDatabase
import logging
from pathlib import Path

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class Neo4jClient:
    def __init__(self, config_path: str = "agents/graphRAG/config/graph_db_config.yml"):
        """
        Initialize Neo4jClient using credentials from a YAML configuration.
        """
        self.config_path = Path(config_path)
        if not self.config_path.exists():
            raise FileNotFoundError(f"Neo4j config file not found at {self.config_path}")

        # Load YAML
        with open(self.config_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)

        neo4j_cfg = cfg.get("neo4j", {})
        self.uri = neo4j_cfg.get("uri", "bolt://localhost:7687")
        self.user = neo4j_cfg.get("user", "neo4j")
        self.password = neo4j_cfg.get("password", "")

        # Connect
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        logger.info(f"Connected to Neo4j at {self.uri} as {self.user}")

        # Optionally create indexes if specified
        if cfg.get("indexes", {}).get("create_on_start", False):
            self.create_indexes()

    def close(self):
        self.driver.close()
        logger.info("Neo4j connection closed.")

    def create_indexes(self) -> None:
        """Create helpful indexes for commonly queried unique keys."""
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
                    logger.info(f"Index query executed: {q}")
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
            raise

    def merge_node(self, label, properties, unique_key=None):
        """
        Merge a node using its unique key and update other properties.
        """
        if unique_key is None:
            raise ValueError("unique_key must be specified for MERGE")
        if unique_key not in properties or properties[unique_key] is None:
            raise ValueError(f"unique_key '{unique_key}' missing or None in properties: {properties}")

        merge_value = properties[unique_key]
        set_props = {k: v for k, v in properties.items() if k != unique_key and v is not None}

        merge_str = f"{unique_key}: ${unique_key}"
        set_str = ", ".join([f"n.{k} = ${k}" for k in set_props.keys()])

        query = f"""
        MERGE (n:{label} {{ {merge_str} }})
        {"SET " + set_str if set_props else ""}
        RETURN elementId(n)
        """

        params = {unique_key: merge_value}
        params.update(set_props)

        try:
            with self.driver.session() as s:
                s.run(query, **params)
        except Exception as e:
            logger.error(f"Error merging node {label} ({unique_key}={merge_value}): {e}")
            raise

    def merge_rel(self, type, from_label, from_props, to_label, to_props, rel_props=None):
        """
        Merge a relationship between two nodes with optional properties.
        """
        rel_props = rel_props or {}
        fp = ", ".join([f"{k}: $fp_{k}" for k, v in from_props.items() if v is not None])
        tp = ", ".join([f"{k}: $tp_{k}" for k, v in to_props.items() if v is not None])
        rp = ", ".join([f"{k}: $rp_{k}" for k, v in rel_props.items() if v is not None])
        rel_clause = f"{{ {rp} }}" if rp else ""

        query = f"""
        MATCH (a:{from_label} {{ {fp} }})
        MATCH (b:{to_label} {{ {tp} }})
        MERGE (a)-[r:{type} {rel_clause}]->(b)
        """

        params = {f"fp_{k}": v for k, v in from_props.items() if v is not None}
        params.update({f"tp_{k}": v for k, v in to_props.items() if v is not None})
        params.update({f"rp_{k}": v for k, v in rel_props.items() if v is not None})

        try:
            with self.driver.session() as s:
                s.run(query, **params)
        except Exception as e:
            logger.error(f"Error merging relationship {type} from {from_label} to {to_label}: {e}")
            raise
