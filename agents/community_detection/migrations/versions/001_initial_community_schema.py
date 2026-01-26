"""
Migration 001: Initial Community Detection Schema

Establishes the baseline schema for community detection:
- Community node constraints and indexes
- Tool node constraints (if not exists)
"""
from agents.community_detection.migrations.base import Migration


class Migration001InitialCommunitySchema(Migration):
    """Initial schema setup for Community Detection service."""
    
    version = "001"
    description = "Initial Community Detection schema - constraints and indexes"
    
    def upgrade(self, session) -> None:
        # Community node constraints
        session.run("""
            CREATE CONSTRAINT community_id_unique IF NOT EXISTS
            FOR (c:Community) REQUIRE c.id IS UNIQUE
        """)
        
        # Community indexes for common queries
        session.run("""
            CREATE INDEX community_level IF NOT EXISTS
            FOR (c:Community) ON (c.level)
        """)
        
        session.run("""
            CREATE INDEX community_uuid IF NOT EXISTS
            FOR (c:Community) ON (c.uuid)
        """)
        
        # Tool constraint (may already exist from other loaders)
        try:
            session.run("""
                CREATE CONSTRAINT tool_id_unique IF NOT EXISTS
                FOR (t:Tool) REQUIRE t.tool_id IS UNIQUE
            """)
        except Exception as e:
            msg = str(e)
            if "IndexAlreadyExists" in msg or "Constraint conflicts with already existing index" in msg:
                print("    ! Found conflicting index on Tool(tool_id). Dropping plain index to upgrade to Unique Constraint...")
                
                indexes = session.run("SHOW INDEXES YIELD name, labelsOrTypes, properties").data()
                for idx in indexes:
                    labels = idx.get("labelsOrTypes") or []
                    props = idx.get("properties") or []
                    
                    if "Tool" in labels and "tool_id" in props:
                        idx_name = idx["name"]
                        if idx_name != "tool_id_unique": # Don't drop the constraint if it partially exists
                            print(f"      Dropping old index: {idx_name}")
                            session.run(f"DROP INDEX {idx_name}")
                
                # Retry constraint creation
                session.run("""
                    CREATE CONSTRAINT tool_id_unique IF NOT EXISTS
                    FOR (t:Tool) REQUIRE t.tool_id IS UNIQUE
                """)
            else:
                raise e
    
    def downgrade(self, session) -> None:
        # Remove indexes first
        session.run("DROP INDEX community_level IF EXISTS")
        session.run("DROP INDEX community_uuid IF EXISTS")
        
        # Remove constraints
        session.run("DROP CONSTRAINT community_id_unique IF EXISTS")
        # Keep tool constraint as it may be used by other services
