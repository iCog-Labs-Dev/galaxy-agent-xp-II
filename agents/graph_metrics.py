"""
Graph structural metrics for the loaded Galaxy graph using Neo4j GDS.
Runs as a standalone script (no FastAPI) and prints JSON to stdout.
"""

import argparse
import json
import os
from collections import Counter
from typing import Dict, Sequence

from neo4j import GraphDatabase

DEFAULT_NODE_LABELS = [
    "Category",
    "Workflow",
    "Step",
    "Tool",
    "ToolInput",
    "ToolOutput",
    "Input",
    "Output",
]

DEFAULT_REL_TYPES = [
    "HAS_WORKFLOW",
    "HAS_STEP",
    "STEP_REQUIRES",
    "STEP_GENERATES",
    "FEEDS_INTO",
    "WORKFLOW_USES_TOOL",
    "STEP_USES_TOOL",
    "HAS_TOOL",
    "TOOL_HAS_INPUT",
    "TOOL_HAS_OUTPUT",
]


class GraphMetricsRunner:
    def __init__(
        self,
        uri: str,
        user: str,
        password: str,
        node_labels: Sequence[str],
        rel_types: Sequence[str],
        orientation: str = "UNDIRECTED",
    ) -> None:
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.node_labels = list(node_labels)
        self.rel_types = list(rel_types)
        self.orientation = orientation
        self.graph_name = "metrics_tmp"

    def close(self) -> None:
        self.driver.close()

    def _run_query(self, query: str, params: Dict | None = None):
        with self.driver.session() as session:
            return list(session.run(query, params or {}))

    def _rel_projection(self) -> Dict:
        return {rel: {"type": rel, "orientation": self.orientation} for rel in self.rel_types}

    def _drop_graph(self) -> None:
        drop_q = "CALL gds.graph.drop($name, false) YIELD graphName RETURN graphName"
        try:
            self._run_query(drop_q, {"name": self.graph_name})
        except Exception:
            # Ignore if it does not exist
            pass

    def _project_graph(self) -> None:
        # Drop if exists
        self._drop_graph()
        proj_q = """
        CALL gds.graph.project(
          $name,
          $nodeLabels,
          $relProjection
        )
        YIELD graphName, nodeCount, relationshipCount
        RETURN graphName, nodeCount, relationshipCount
        """
        self._run_query(
            proj_q,
            {
                "name": self.graph_name,
                "nodeLabels": self.node_labels,
                "relProjection": self._rel_projection(),
            },
        )

    def _estimate_global_clustering(self) -> float | None:
        """Estimate global clustering coefficient via triangleCount and degree.

        Uses the identity: C_global = (sum_i triangleCount_i) / (sum_i k_i choose 2).
        Note: sum_i triangleCount_i counts each triangle three times, so numerator = 3T.
        """
        tri_q = """
        CALL gds.triangleCount.stream($graph)
        YIELD triangleCount
        RETURN toFloat(sum(triangleCount)) AS triSum
        """
        wedge_q = """
        CALL gds.degree.stream($graph)
        YIELD score
        RETURN toFloat(sum(score * (score - 1))) / 2.0 AS wedges
        """
        try:
            tri_row = self._run_query(tri_q, {"graph": self.graph_name})[0]
            wedge_row = self._run_query(wedge_q, {"graph": self.graph_name})[0]
            tri_sum = float(tri_row["triSum"]) if tri_row["triSum"] is not None else 0.0
            wedges = float(wedge_row["wedges"]) if wedge_row["wedges"] is not None else 0.0
            if wedges <= 0.0:
                return None
            return tri_sum / wedges
        except Exception:
            return None

    def degree_distribution(self) -> Dict:
        # GDS degree histogram on projected graph
        query = """
        CALL gds.degree.stream($graph)
        YIELD score
        RETURN score AS degree, count(*) AS frequency
        ORDER BY degree
        """
        try:
            rows = self._run_query(query, {"graph": self.graph_name})
            bins = [{"degree": int(r["degree"]), "frequency": int(r["frequency"])} for r in rows]
            return {"bins": bins}
        except Exception as e:  # Fallback to pure Cypher
            cypher = """
            MATCH (n)
            WHERE any(l IN labels(n) WHERE l IN $labels)
            WITH count { (n)--() } AS degree
            RETURN degree, count(*) AS frequency
            ORDER BY degree
            """
            rows = self._run_query(cypher, {"labels": self.node_labels})
            bins = [{"degree": int(r["degree"]), "frequency": int(r["frequency"])} for r in rows]
            return {"bins": bins, "fallback": str(e)}

    def clustering(self) -> Dict:
        local_q = """
        CALL gds.localClusteringCoefficient.stream($graph)
        YIELD localClusteringCoefficient AS c
        RETURN avg(c) AS avg, stDev(c) AS stdev, min(c) AS min, max(c) AS max,
               percentileCont(c, 0.5) AS p50
        """
        global_q = """
        CALL gds.globalClusteringCoefficient.stream($graph)
        YIELD globalClusteringCoefficient AS gcc
        RETURN gcc
        """
        try:
            local_row = self._run_query(local_q, {"graph": self.graph_name})[0]
            local_metrics = {
                "avg": float(local_row["avg"]),
                "stdev": float(local_row["stdev"]),
                "min": float(local_row["min"]),
                "max": float(local_row["max"]),
                "p50": float(local_row["p50"]),
            }

            global_value = None
            global_fallback = None
            try:
                global_row = self._run_query(global_q, {"graph": self.graph_name})[0]
                global_value = float(global_row["gcc"])
            except Exception as ge:
                # Try estimating global coefficient from triangleCount and degree
                estimate = self._estimate_global_clustering()
                if estimate is not None:
                    global_value = estimate
                    global_fallback = "estimated via triangleCount/degree"
                else:
                    global_fallback = str(ge)

            result = {"local": local_metrics, "global": global_value}
            if global_fallback:
                result["global_fallback"] = global_fallback
            return result
        except Exception as e:  # Fallback: triangle density proxy
            triangle_q = """
            MATCH (a)--(b)--(c)--(a)
            WHERE id(a) < id(b) AND id(b) < id(c)
            RETURN count(*) AS triangles
            """
            tri = self._run_query(triangle_q)[0]["triangles"]
            return {"triangles": int(tri), "fallback": str(e)}

    def motifs(self, hub_threshold: int = 5) -> Dict:
        triangle_q = """
        MATCH (a)--(b)--(c)--(a)
        WHERE id(a) < id(b) AND id(b) < id(c)
        RETURN count(*) AS triangles
        """
        open_q = """
        MATCH (a)--(b)--(c)
        WHERE NOT (a)--(c)
        RETURN count(*) AS openTriads
        """
        hubs_q = """
        MATCH (center)-[]-(leaf)
        WHERE any(l IN labels(center) WHERE l IN $labels)
          AND any(l IN labels(leaf) WHERE l IN $labels)
        WITH center, count(leaf) AS deg
        WHERE deg >= $threshold
        RETURN elementId(center) AS id, deg
        ORDER BY deg DESC
        LIMIT 25
        """
        rows_tri = self._run_query(triangle_q)
        rows_open = self._run_query(open_q)
        rows_hubs = self._run_query(hubs_q, {"labels": self.node_labels, "threshold": hub_threshold})
        hubs = [{"node": r["id"], "degree": int(r["deg"])} for r in rows_hubs]
        return {
            "triangles": int(rows_tri[0]["triangles"]),
            "openTriads": int(rows_open[0]["openTriads"]),
            "hubs": hubs,
        }

    def block_separability(self) -> Dict:
        louvain_q = """
        CALL gds.louvain.stream($graph)
        YIELD nodeId, communityId
        RETURN gds.util.asNode(nodeId) AS n, communityId
        """
        rows = self._run_query(louvain_q, {"graph": self.graph_name})
        mapping = {str(r["n"].element_id): int(r["communityId"]) for r in rows}
        if not mapping:
            return {"communities": []}

        sizes = Counter(mapping.values())

        edge_q = """
        MATCH (a)-[r]-(b)
        WHERE id(a) < id(b)
          AND type(r) IN $rel_types
          AND any(l IN labels(a) WHERE l IN $labels)
          AND any(l IN labels(b) WHERE l IN $labels)
        RETURN elementId(a) AS a, elementId(b) AS b
        """
        edges = self._run_query(edge_q, {"rel_types": self.rel_types, "labels": self.node_labels})

        internal = Counter()
        external = Counter()
        for rec in edges:
            a = rec["a"]
            b = rec["b"]
            ca = mapping.get(a)
            cb = mapping.get(b)
            if ca is None or cb is None:
                continue
            if ca == cb:
                internal[ca] += 1
            else:
                external[ca] += 1
                external[cb] += 1

        communities = []
        for cid, size in sizes.most_common():
            communities.append({
                "communityId": cid,
                "size": int(size),
                "internalEdges": int(internal.get(cid, 0)),
                "externalEdges": int(external.get(cid, 0)),
            })
        return {"communities": communities}

    def run_all(self, hub_threshold: int = 5) -> Dict:
        self._project_graph()
        try:
            degree = self.degree_distribution()
            clustering = self.clustering()
            motifs = self.motifs(hub_threshold=hub_threshold)
            blocks = self.block_separability()
            return {
                "degree": degree,
                "clustering": clustering,
                "motifs": motifs,
                "blocks": blocks,
            }
        finally:
            self._drop_graph()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute graph metrics via Neo4j GDS")
    parser.add_argument("--uri", default=os.getenv("NEO4J_URI", "bolt://localhost:7687"))
    parser.add_argument("--user", default=os.getenv("NEO4J_USER", "neo4j"))
    parser.add_argument("--password", default=os.getenv("NEO4J_PASSWORD", "password"))
    parser.add_argument(
        "--node-labels",
        help="Comma-separated node labels to include",
        default=",".join(DEFAULT_NODE_LABELS),
    )
    parser.add_argument(
        "--rel-types",
        help="Comma-separated relationship types to include",
        default=",".join(DEFAULT_REL_TYPES),
    )
    parser.add_argument("--orientation", default="UNDIRECTED", choices=["UNDIRECTED", "NATURAL", "REVERSE"])
    parser.add_argument("--hub-threshold", type=int, default=5, help="Degree threshold for hub motif")
    parser.add_argument("--output", help="Optional path to write JSON report; prints to stdout if omitted")
    parser.add_argument("--no-pretty", action="store_true", help="Disable pretty-printing (compact JSON)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    node_labels = [s for s in args.node_labels.split(",") if s]
    rel_types = [s for s in args.rel_types.split(",") if s]

    runner = GraphMetricsRunner(
        uri=args.uri,
        user=args.user,
        password=args.password,
        node_labels=node_labels,
        rel_types=rel_types,
        orientation=args.orientation,
    )
    try:
        metrics = runner.run_all(hub_threshold=args.hub_threshold)
        indent = None if args.no_pretty else 2
        rendered = json.dumps(metrics, indent=indent, ensure_ascii=False)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(rendered)
                f.write("\n")
        else:
            print(rendered)
    finally:
        runner.close()


if __name__ == "__main__":
    main()
