"""
Migration 003: Community Summaries

Adds schema support for LLM-generated community summaries:
- name: Short title for the community
- summary: Detailed description
- Full-text search index for semantic queries
"""
from agents.community_detection.migrations.base import Migration


class Migration003CommunitySummaries(Migration):
    """Schema for community summary fields and search indexes."""
    
    version = "003"
    description = "Community summary fields with full-text search"
    
    def upgrade(self, session) -> None:
        # Create full-text index for community search
        try:
            session.run("""
                CREATE FULLTEXT INDEX community_search IF NOT EXISTS
                FOR (c:Community) ON EACH [c.name, c.summary]
            """)
        except Exception as e:
            print(f"    Note: Could not create fulltext index: {e}")
        
        # Create index on community name for quick lookups
        session.run("""
            CREATE INDEX community_name IF NOT EXISTS
            FOR (c:Community) ON (c.name)
        """)
    
    def downgrade(self, session) -> None:
        # Drop fulltext index
        try:
            session.run("DROP INDEX community_search IF EXISTS")
        except Exception:
            pass
        
        # Drop name index
        session.run("DROP INDEX community_name IF EXISTS")
