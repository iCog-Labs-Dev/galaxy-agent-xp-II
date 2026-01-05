"""
Migration Runner - Executes and tracks Neo4j schema migrations.

Handles:
- Discovering available migrations
- Tracking applied migrations in Neo4j
- Running upgrades and downgrades
- Validation and status reporting
"""
import os
import importlib
import importlib.util
from datetime import datetime
from typing import List, Optional, Type
from neo4j import Driver

from .base import Migration, MigrationInfo


class MigrationRunner:
    """
    Orchestrates schema migration execution for Neo4j.
    
    Migrations are tracked via SchemaMigration nodes in the database.
    """
    
    MIGRATION_LABEL = "SchemaMigration"
    
    def __init__(self, driver: Driver):
        self.driver = driver
        self._migrations_cache: Optional[List[Type[Migration]]] = None
    
    def _ensure_migration_tracking(self, session) -> None:
        """Create the migration tracking constraint if it doesn't exist."""
        session.run(f"""
            CREATE CONSTRAINT schema_migration_version IF NOT EXISTS
            FOR (m:{self.MIGRATION_LABEL}) REQUIRE m.version IS UNIQUE
        """)
    
    def _get_applied_migrations(self, session) -> dict:
        """Get all migrations that have been applied to the database."""
        result = session.run(f"""
            MATCH (m:{self.MIGRATION_LABEL})
            RETURN m.version AS version, m.description AS description, 
                   m.applied_at AS applied_at, m.checksum AS checksum
            ORDER BY m.version
        """)
        
        applied = {}
        for record in result:
            applied[record["version"]] = MigrationInfo(
                version=record["version"],
                description=record["description"],
                applied_at=record["applied_at"],
                checksum=record["checksum"]
            )
        return applied
    
    def _record_migration(self, session, migration: Migration) -> None:
        """Record that a migration has been applied."""
        session.run(f"""
            CREATE (m:{self.MIGRATION_LABEL} {{
                version: $version,
                description: $description,
                applied_at: datetime(),
                checksum: $checksum
            }})
        """, 
            version=migration.version,
            description=migration.description,
            checksum=migration.get_checksum()
        )
    
    def _remove_migration_record(self, session, version: str) -> None:
        """Remove a migration record (for downgrades)."""
        session.run(f"""
            MATCH (m:{self.MIGRATION_LABEL} {{version: $version}})
            DELETE m
        """, version=version)
    
    def discover_migrations(self) -> List[Type[Migration]]:
        """Discover all migration classes in the versions directory."""
        if self._migrations_cache is not None:
            return self._migrations_cache
        
        migrations = []
        versions_dir = os.path.join(os.path.dirname(__file__), "versions")
        
        if not os.path.exists(versions_dir):
            return migrations
        
        for filename in sorted(os.listdir(versions_dir)):
            if filename.endswith(".py") and not filename.startswith("_"):
                module_path = os.path.join(versions_dir, filename)
                module_name = filename[:-3]
                
                spec = importlib.util.spec_from_file_location(module_name, module_path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Find Migration subclasses in the module
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (isinstance(attr, type) and 
                            issubclass(attr, Migration) and 
                            attr is not Migration and
                            hasattr(attr, 'version') and attr.version):
                            migrations.append(attr)
        
        # Sort by version
        migrations.sort(key=lambda m: m.version)
        self._migrations_cache = migrations
        return migrations
    
    def get_status(self) -> List[dict]:
        """Get the status of all migrations."""
        with self.driver.session() as session:
            self._ensure_migration_tracking(session)
            applied = self._get_applied_migrations(session)
        
        migrations = self.discover_migrations()
        status = []
        
        for migration_cls in migrations:
            version = migration_cls.version
            info = applied.get(version)
            
            status.append({
                "version": version,
                "description": migration_cls.description,
                "applied": info is not None,
                "applied_at": info.applied_at if info else None,
                "checksum_match": (
                    info.checksum == migration_cls().get_checksum() 
                    if info else None
                )
            })
        
        return status
    
    def is_up_to_date(self) -> bool:
        """Check if all migrations have been applied."""
        status = self.get_status()
        return all(s["applied"] for s in status)
    
    def upgrade(self, target: Optional[str] = None) -> List[str]:
        """
        Apply pending migrations up to the target version.
        
        Args:
            target: Version to migrate to. If None, applies all pending.
        
        Returns:
            List of applied migration versions.
        """
        with self.driver.session() as session:
            self._ensure_migration_tracking(session)
            applied = self._get_applied_migrations(session)
        
        migrations = self.discover_migrations()
        applied_versions = []
        
        for migration_cls in migrations:
            version = migration_cls.version
            
            # Skip if already applied
            if version in applied:
                continue
            
            # Stop if we've reached the target
            if target and version > target:
                break
            
            print(f"  Applying migration {version}: {migration_cls.description}...")
            
            migration = migration_cls()
            with self.driver.session() as session:
                try:
                    migration.upgrade(session)
                    self._record_migration(session, migration)
                    applied_versions.append(version)
                    print(f"  ✓ Applied {version}")
                except Exception as e:
                    print(f"  ✗ Failed to apply {version}: {e}")
                    raise
        
        return applied_versions
    
    def downgrade(self, target: str) -> List[str]:
        """
        Rollback migrations down to (but not including) the target version.
        
        Args:
            target: Version to rollback to.
        
        Returns:
            List of rolled-back migration versions.
        """
        with self.driver.session() as session:
            self._ensure_migration_tracking(session)
            applied = self._get_applied_migrations(session)
        
        migrations = self.discover_migrations()
        
        # Get migrations to rollback (in reverse order)
        to_rollback = []
        for migration_cls in reversed(migrations):
            version = migration_cls.version
            if version in applied and version > target:
                to_rollback.append(migration_cls)
        
        rolled_back = []
        for migration_cls in to_rollback:
            version = migration_cls.version
            print(f"  Rolling back migration {version}: {migration_cls.description}...")
            
            migration = migration_cls()
            with self.driver.session() as session:
                try:
                    migration.downgrade(session)
                    self._remove_migration_record(session, version)
                    rolled_back.append(version)
                    print(f"  ✅ Rolled back {version}")
                except Exception as e:
                    print(f"  ❌ Failed to rollback {version}: {e}")
                    raise
        
        return rolled_back
