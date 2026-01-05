import os
import sys
import argparse
from datetime import datetime
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.community_detection.migrations.runner import MigrationRunner

load_dotenv()


def get_driver():
    """Create Neo4j driver from environment variables."""
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "abc12345")
    return GraphDatabase.driver(uri, auth=(user, password))


def cmd_status(args):
    """Show the current migration status."""
    driver = get_driver()
    try:
        runner = MigrationRunner(driver)
        status = runner.get_status()
        
        if not status:
            print("\n  No migrations found.")
            return
        
        print("\n  Migration Status")
        print("  " + "=" * 60)
        
        for migration in status:
            if migration["applied"]:
                checksum = "✓" if migration["checksum_match"] else "⚠ modified"
                applied = migration["applied_at"]
                if hasattr(applied, 'strftime'):
                    applied_str = applied.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    applied_str = str(applied)[:19]
                print(f"  ✅ {migration['version']} - {migration['description']}")
                print(f"      Applied: {applied_str} {checksum}")
            else:
                print(f"  ⏰ {migration['version']} - {migration['description']}")
                print(f"      Status: pending")
        
        print()
        
        if runner.is_up_to_date():
            print("  ✅ Database is up to date.\n")
        else:
            pending = sum(1 for m in status if not m["applied"])
            print(f"  ⚠️ {pending} pending migration(s). Run 'migrate upgrade' to apply.\n")
    finally:
        driver.close()


def cmd_upgrade(args):
    """Apply pending migrations."""
    driver = get_driver()
    try:
        runner = MigrationRunner(driver)
        
        print("\n  Upgrading database schema...")
        print("  " + "-" * 40)
        
        target = args.target if hasattr(args, 'target') and args.target else None
        applied = runner.upgrade(target)
        
        if applied:
            print("  " + "-" * 40)
            print(f"  Applied {len(applied)} migration(s): {', '.join(applied)}\n")
        else:
            print("  No pending migrations to apply.\n")
    finally:
        driver.close()


def cmd_downgrade(args):
    """Rollback migrations to a target version."""
    if not args.target:
        print("\n  Error: Please specify a target version to rollback to.")
        print("  Example: migrate downgrade 001\n")
        return
    
    driver = get_driver()
    try:
        runner = MigrationRunner(driver)
        
        print(f"\n  Rolling back to version {args.target}...")
        print("  " + "-" * 40)
        
        rolled_back = runner.downgrade(args.target)
        
        if rolled_back:
            print("  " + "-" * 40)
            print(f"  Rolled back {len(rolled_back)} migration(s): {', '.join(rolled_back)}\n")
        else:
            print("  No migrations to rollback.\n")
    finally:
        driver.close()


def cmd_create(args):
    """Create a new migration file from template."""
    if not args.name:
        print("\n  Error: Please specify a migration name.")
        print("  Example: migrate create add_new_index\n")
        return
    
    # Find next version number
    versions_dir = os.path.join(os.path.dirname(__file__), "migrations", "versions")
    os.makedirs(versions_dir, exist_ok=True)
    
    existing = [f for f in os.listdir(versions_dir) 
                if f.endswith(".py") and not f.startswith("_")]
    
    if existing:
        last_version = max(int(f[:3]) for f in existing if f[:3].isdigit())
        next_version = f"{last_version + 1:03d}"
    else:
        next_version = "001"
    
    # Sanitize name
    name = args.name.lower().replace(" ", "_").replace("-", "_")
    filename = f"{next_version}_{name}.py"
    filepath = os.path.join(versions_dir, filename)
    
    # Generate class name
    class_name = "Migration" + next_version + "".join(
        word.capitalize() for word in name.split("_")
    )
    
    template = f'''"""
Migration {next_version}: {args.name.replace("_", " ").title()}

Description of what this migration does.
"""
from agents.community_detection.migrations.base import Migration


class {class_name}(Migration):
    """Description of this migration."""
    
    version = "{next_version}"
    description = "{args.name.replace("_", " ").title()}"
    
    def upgrade(self, session) -> None:
        # Add your upgrade logic here
        # Example:
        # session.run("""
        #     CREATE INDEX new_index IF NOT EXISTS
        #     FOR (n:Label) ON (n.property)
        # """)
        pass
    
    def downgrade(self, session) -> None:
        # Add your downgrade logic here
        # Example:
        # session.run("DROP INDEX new_index IF EXISTS")
        pass
'''
    
    with open(filepath, "w") as f:
        f.write(template)
    
    print(f"\n  Created migration: {filename}")
    print(f"  Path: {filepath}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Community Detection Schema Migration Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python migrate.py status              Show migration status
  python migrate.py upgrade             Apply all pending migrations
  python migrate.py upgrade 002         Apply migrations up to version 002
  python migrate.py downgrade 001       Rollback to version 001
  python migrate.py create add_index    Create a new migration
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Status command
    subparsers.add_parser("status", help="Show current migration status")
    
    # Upgrade command
    upgrade_parser = subparsers.add_parser("upgrade", help="Apply pending migrations")
    upgrade_parser.add_argument("target", nargs="?", help="Target version (optional)")
    
    # Downgrade command
    downgrade_parser = subparsers.add_parser("downgrade", help="Rollback migrations")
    downgrade_parser.add_argument("target", help="Target version to rollback to")
    
    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new migration")
    create_parser.add_argument("name", help="Name for the new migration")
    
    args = parser.parse_args()
    
    if args.command == "status":
        cmd_status(args)
    elif args.command == "upgrade":
        cmd_upgrade(args)
    elif args.command == "downgrade":
        cmd_downgrade(args)
    elif args.command == "create":
        cmd_create(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
