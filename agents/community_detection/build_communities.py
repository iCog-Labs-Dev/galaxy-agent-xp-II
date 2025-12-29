import os
import sys
import igraph as ig
import leidenalg
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

# Configuration
URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
AUTH = (os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "abc12345"))

RESOLUTIONS = [1.5, 0.2]


class CommunityBuilder:
    def __init__(self, uri, auth):
        self.driver = GraphDatabase.driver(uri, auth=auth)

    def close(self):
        self.driver.close()

    def reset_graph(self):
        print("Cleaning up Community Data")

        with self.driver.session() as session:
            session.run("MATCH (c:Community) DETACH DELETE c")
            session.run("MATCH ()-[r:USED_WITH]-() DELETE r")
        print("Cleanup complete.")

    def normalize_graph(self):
        print("\nGraph Normalization (Fixing Schema Gaps)")
        with self.driver.session() as session:
            print("Materializing 'USES_TOOL' relationships...")
            query_link_tools = """
            MATCH (s:Step)
            WHERE s.tool_id IS NOT NULL AND NOT (s)-[:USES_TOOL]->(:Tool)
            MATCH (t:Tool) 
            WHERE t.tool_id = s.tool_id OR t.tool_id = s.tool_uuid
            MERGE (s)-[r:USES_TOOL]->(t)
            RETURN count(r) as created
            """
            result = session.run(query_link_tools)
            count = result.single()["created"]
            print(f"      Fixed: Created {count} missing 'USES_TOOL' edges.")

    def build_topology(self):
        print("Build Weighted Topology ...")

        with self.driver.session() as session:
            check = session.run(
                """
                MATCH (w:Workflow)-[:HAS_STEP]->(s:Step)-[:USES_TOOL]->(t:Tool) 
                RETURN count(w) as count
            """
            ).single()["count"]

            if check == 0:
                print(
                    "❌ CRITICAL ERROR: No 'HAS_STEP' or 'USES_TOOL' relationships found."
                )
                print(
                    "   Did you load the data? Check if relationship names match schema_relationships.py."
                )
                return
            else:
                print(f" (Debug: Found {check} paths to process)")

            # TODO: Fix the flow relationship
            # print("Calculating Direct Data Flow (Strong Links)...")
            # query_flow = """
            # MATCH (t1:Tool)<-[:USES_TOOL]-(s1:Step)-[:HAS_OUTPUT]->(:Output)-[:FEEDS]->(:Input)<-[:HAS_INPUT]-(s2:Step)-[:USES_TOOL]->(t2:Tool)
            # WHERE elementId(t1) <> elementId(t2)
            # WITH t1, t2, count(*) as flow
            # MERGE (t1)-[r:USED_WITH]-(t2)
            # ON CREATE SET r.weight = flow * 10
            # ON MATCH SET r.weight = r.weight + (flow * 10)
            # RETURN count(r) as edges
            # """

            # flow_result = session.run(query_flow).single()
            # flow_count = flow_result["edges"] if flow_result else 0
            # print(f"      Created {flow_count} flow edges.")

            query_cooccur = """
            MATCH (w:Workflow)-[:HAS_STEP]->(s1:Step)-[:USES_TOOL]->(t1:Tool)
            MATCH (w)-[:HAS_STEP]->(s2:Step)-[:USES_TOOL]->(t2:Tool)
            WHERE elementId(t1) < elementId(t2)
            
            WITH t1, t2, count(DISTINCT w) as co_occurrence
            
            MERGE (t1)-[r:USED_WITH]-(t2)
            ON CREATE SET r.weight = co_occurrence       
            ON MATCH SET r.weight = r.weight + co_occurrence
            RETURN count(r) as edges
            """

            co_result = session.run(query_cooccur).single()
            co_count = co_result["edges"] if co_result else 0
            print(f"Created/Updated {co_count} co-occurrence edges.")

        print("Topology edges built.")

    def run_hierarchical_leiden(self):
        print("Running Recursive Leiden ... ")

        with self.driver.session() as session:
            # Load connected tools
            nodes = session.run(
                "MATCH (t:Tool) WHERE (t)-[:USED_WITH]-() RETURN t.tool_id as id"
            ).value()
            if not nodes:
                print("❌ No tools connected. Topology build likely failed.")
                return

            node_map = {node_id: i for i, node_id in enumerate(nodes)}
            reverse_map = {i: node_id for i, node_id in enumerate(nodes)}

            result = session.run(
                """
                MATCH (t1:Tool)-[r:USED_WITH]-(t2:Tool)
                RETURN t1.tool_id as src, t2.tool_id as tgt, r.weight as w
            """
            )
            edges = []
            weights = []
            for r in result:
                if r["src"] in node_map and r["tgt"] in node_map:
                    edges.append((node_map[r["src"]], node_map[r["tgt"]]))
                    val = r["w"]
                    weights.append(float(val) if val is not None else 1.0)

        print(f"Graph Loaded: {len(nodes)} nodes, {len(edges)} edges.")

        if not edges:
            print("Error: No edges to cluster.")
            return

        g = ig.Graph(len(nodes), edges=edges)
        g.es["weight"] = weights

        hierarchy_memberships = []

        current_graph = g
        for level, res in enumerate(RESOLUTIONS):
            print(f"Running Leiden Level {level} (Resolution={res})...")

            if not isinstance(current_graph, ig.Graph):
                if hasattr(current_graph, "graph"):
                    current_graph = current_graph.graph

            if "weight" in current_graph.es.attributes():
                w = current_graph.es["weight"]
            else:
                w = None

            partition = leidenalg.find_partition(
                current_graph,
                leidenalg.RBConfigurationVertexPartition,
                weights=w,
                resolution_parameter=res,
            )
            hierarchy_memberships.append(partition.membership)
            print(f"Found {len(set(partition.membership))} clusters.")

            if level < len(RESOLUTIONS) - 1:
                current_graph = partition.aggregate_partition()

        self._write_hierarchy(reverse_map, hierarchy_memberships)

    def _write_hierarchy(self, tool_map, hierarchy_memberships):
        print("Saving to Neo4J ... ")

        if len(hierarchy_memberships) < 2:
            print("❌ Error: Did not generate enough hierarchy levels.")
            return

        updates = []

        for tool_idx, tool_uuid in tool_map.items():
            l0_cluster_id = hierarchy_memberships[0][tool_idx]

            try:
                l1_cluster_id = hierarchy_memberships[1][l0_cluster_id]
            except IndexError:
                # Fallback if hierarchy incomplete
                l1_cluster_id = 0

            updates.append(
                {
                    "tool_id": tool_uuid,
                    "l0_id": f"comm_L0_{l0_cluster_id}",
                    "l1_id": f"comm_L1_{l1_cluster_id}",
                }
            )

        query = """
        UNWIND $batch as row
        MATCH (t:Tool {tool_id: row.tool_id})
        
        // Create L1 
        MERGE (c1:Community {id: row.l1_id})
        ON CREATE SET c1.level = 1, c1.uuid = row.l1_id
        
        // Create L0 
        MERGE (c0:Community {id: row.l0_id})
        ON CREATE SET c0.level = 0, c0.uuid = row.l0_id
        
        // Relationships
        MERGE (c1)-[:IS_PARENT_OF]->(c0)
        MERGE (t)-[:IN_COMMUNITY]->(c0)
        """

        with self.driver.session() as session:
            batch_size = 2000
            for i in range(0, len(updates), batch_size):
                session.run(query, batch=updates[i : i + batch_size])
                print(f"Wrote batch {i}")

        print("Hierarchy saved.")


if __name__ == "__main__":
    builder = CommunityBuilder(URI, AUTH)
    builder.reset_graph()
    builder.normalize_graph()
    builder.build_topology()
    builder.run_hierarchical_leiden()
    builder.close()
