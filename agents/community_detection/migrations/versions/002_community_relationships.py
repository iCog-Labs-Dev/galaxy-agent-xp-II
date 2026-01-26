"""
Migration 002: Community Relationship Types

Documents and ensures proper relationship schema for:
- USED_WITH: Tool co-occurrence relationships (weighted)
- IN_COMMUNITY: Tool membership in communities
- IS_PARENT_OF: Community hierarchy (L1 -> L0)
"""
from agents.community_detection.migrations.base import Migration


class Migration002CommunityRelationships(Migration):
    """Schema for community-related relationships."""
    
    version = "002"
    description = "Community relationship types - USED_WITH, IN_COMMUNITY, IS_PARENT_OF"
    
    def upgrade(self, session) -> None:
        # Create relationship type index for USED_WITH weight lookups
        try:
            session.run("""
                CREATE INDEX used_with_weight IF NOT EXISTS
                FOR ()-[r:USED_WITH]-() ON (r.weight)
            """)
        except Exception:
            # Older Neo4j versions may not support this
            pass
        
        # Ensure USES_TOOL relationship pattern exists
        
        
        # Create a schema documentation node
        session.run("""
            MERGE (s:SchemaDoc {name: 'community_relationships'})
            SET s.relationships = [
                'USED_WITH: (Tool)-[weight:float]-(Tool) - Co-occurrence in workflows',
                'IN_COMMUNITY: (Tool)->(Community) - Tool membership in L0 cluster',
                'IS_PARENT_OF: (Community L1)->(Community L0) - Hierarchy'
            ],
            s.updated_at = datetime()
        """)
    
    def downgrade(self, session) -> None:
        # Remove relationship index
        try:
            session.run("DROP INDEX used_with_weight IF EXISTS")
        except Exception:
            pass
        
        # Remove documentation node
        session.run("""
            MATCH (s:SchemaDoc {name: 'community_relationships'})
            DELETE s
        """)
