# Community Detection - Database Migrations Guide

This document explains how to use and create database schema migrations for the Community Detection service.

## Quick Start

```bash
# Check migration status
python -m agents.community_detection.migrate status

# Apply all pending migrations
python -m agents.community_detection.migrate upgrade

# Create a new migration
python -m agents.community_detection.migrate create "add_centrality_scores"
```

## Migration Structure

Each migration defines:
- **version**: Sequential number (e.g., "001", "002")
- **description**: Human-readable description
- **upgrade()**: Apply schema changes
- **downgrade()**: Revert schema changes

```python
from agents.community_detection.migrations.base import Migration

class Migration004AddCentrality(Migration):
    version = "004"
    description = "Add centrality scores to communities"
    
    def upgrade(self, session) -> None:
        session.run("""
            CREATE INDEX community_centrality IF NOT EXISTS
            FOR (c:Community) ON (c.centrality)
        """)
    
    def downgrade(self, session) -> None:
        session.run("DROP INDEX community_centrality IF EXISTS")
```

## Best Practices

1. **Idempotency**: Use `IF NOT EXISTS` / `IF EXISTS` clauses
2. **Small changes**: One logical change per migration
3. **Test both directions**: Verify upgrade AND downgrade work
4. **Never modify applied migrations**: Create a new migration instead

## CLI Commands

| Command | Description |
|---------|-------------|
| `status` | Show applied and pending migrations |
| `upgrade [version]` | Apply migrations (optionally to specific version) |
| `downgrade <version>` | Rollback to specified version |
| `create <name>` | Generate new migration template |

## Troubleshooting

**Schema outdated error**: Run `python -m agents.community_detection.migrate upgrade`

**Checksum mismatch**: An applied migration was modified. This can cause issues. Options:
- Revert the file changes
- Manually update the checksum in Neo4j

**Migration failed mid-way**: Check Neo4j browser, fix data issues, then retry.
