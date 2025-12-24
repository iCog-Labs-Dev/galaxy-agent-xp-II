import yaml
from neo4j import GraphDatabase
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
logging.getLogger("neo4j").setLevel(logging.WARNING)


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
        """Create indexes for all unique keys in the schema."""
        queries = [
            "CREATE INDEX IF NOT EXISTS FOR (w:Workflow) ON (w.workflow_id)",
            "CREATE INDEX IF NOT EXISTS FOR (s:Step) ON (s.step_uid)",
            "CREATE INDEX IF NOT EXISTS FOR (t:Tool) ON (t.tool_id)",
            "CREATE INDEX IF NOT EXISTS FOR (c:Category) ON (c.category_id)",
            "CREATE INDEX IF NOT EXISTS FOR (i:ToolInput) ON (i.input_uid)",
            "CREATE INDEX IF NOT EXISTS FOR (o:ToolOutput) ON (o.output_uid)",
            "CREATE INDEX IF NOT EXISTS FOR (k:Keyword) ON (k.name)",
            "CREATE INDEX IF NOT EXISTS FOR (i:WorkflowInput) ON (i.input_id)",
            "CREATE INDEX IF NOT EXISTS FOR (o:WorkflowOutput) ON (o.output_id)",
        ]
        try:
            with self.driver.session() as session:
                for q in queries:
                    session.run(q)
                    logger.info(f"Index executed: {q}")
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
            raise

    # -----------------------------
    # Merge Node
    # -----------------------------
    def merge_node(self, label: str, properties: dict, unique_key: str):
        if unique_key not in properties:
            raise ValueError(f"{unique_key} missing in node {label}")

        clean_props = {k: v for k, v in properties.items() if v is not None}
        merge_key = clean_props[unique_key]
        set_props = {k: v for k, v in clean_props.items() if k != unique_key}

        query = f"""
        MERGE (n:{label} {{ {unique_key}: ${unique_key} }})
        SET n += $props
        """
        try:
            with self.driver.session() as session:
                session.run(query, **{unique_key: merge_key, "props": set_props})
        except Exception as e:
            logger.error(f"Error merging node {label} ({merge_key}): {e}")
            raise

    # -----------------------------
    # Merge Relationship
    # -----------------------------
    def merge_rel(self, type: str, from_label: str, from_props: dict, 
                  to_label: str, to_props: dict, rel_props: Optional[dict] = None):
        """
        Merge a relationship between two nodes, safely handling empty properties.
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
            with self.driver.session() as session:
                session.run(query, **params)
        except Exception as e:
            logger.error(f"Error merging relationship {type} from {from_label} to {to_label}: {e}")
            raise

    # -----------------------------
    # Convenience: Step → Tool
    # -----------------------------
    def merge_step_tool(self, step_props: dict, tool_props: dict):
        if "step_uid" not in step_props or "tool_id" not in tool_props:
            raise ValueError("Step node must have 'step_uid' and Tool node must have 'tool_id'")
        self.merge_rel(
            type="USES_TOOL",
            from_label="Step",
            from_props={"step_uid": step_props["step_uid"]},
            to_label="Tool",
            to_props={"tool_id": tool_props["tool_id"]},
            rel_props=None
        )

    # -----------------------------
    # Run Arbitrary Query
    # -----------------------------
    def run_query(self, cypher: str, parameters: Optional[dict] = None) -> List[dict]:
        parameters = parameters or {}
        try:
            with self.driver.session() as session:
                result = session.run(cypher, parameters)
                return [record.data() for record in result]
        except Exception as e:
            logger.exception(f"Failed to run query: {cypher}")
            raise
