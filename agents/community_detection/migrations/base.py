"""
Base classes and utilities for Neo4j schema migrations.

Inspired by Alembic but tailored for Neo4j graph databases.
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
import hashlib


class Migration(ABC):
    """
    Base class for all schema migrations.
    
    Each migration must define:
    - version: Sequential version number (e.g., "001", "002")
    - description: Human-readable description of the migration
    - upgrade(): Apply the migration
    - downgrade(): Revert the migration
    """
    
    version: str = ""
    description: str = ""
    
    @abstractmethod
    def upgrade(self, session) -> None:
        """Apply the migration to the database."""
        pass
    
    @abstractmethod
    def downgrade(self, session) -> None:
        """Revert the migration from the database."""
        pass
    
    def get_checksum(self) -> str:
        """Generate a checksum for this migration based on its source code."""
        import inspect
        import os
        
        try:
            # Try to read the file content directly
            file_path = inspect.getfile(self.__class__)
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    content = f.read()
                return hashlib.sha256(content).hexdigest()[:16]
            
            # Fallback to getsource if file read fails
            source = inspect.getsource(self.__class__)
            return hashlib.sha256(source.encode()).hexdigest()[:16]
            
        except (TypeError, OSError):
            # If inspection fails completely 
            # Return a hash of class name and description as backup
            fallback = f"{self.__class__.__name__}:{self.description}"
            return hashlib.sha256(fallback.encode()).hexdigest()[:16]


class MigrationInfo:
    """Metadata about a migration stored in Neo4j."""
    
    def __init__(
        self, 
        version: str, 
        description: str, 
        applied_at: Optional[datetime] = None,
        checksum: Optional[str] = None
    ):
        self.version = version
        self.description = description
        self.applied_at = applied_at
        self.checksum = checksum
    
    def __repr__(self):
        status = f"applied {self.applied_at}" if self.applied_at else "pending"
        return f"<Migration {self.version}: {self.description} ({status})>"
