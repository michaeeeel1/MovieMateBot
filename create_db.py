# create_db.py
"""
Database Initialization Script

Creates all database tables.
"""

import sys
import logging
from sqlalchemy import inspect

from database.connection import engine, test_connection
from database.models import Base

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def create_tables() -> bool:
    """Create all database tables"""
    print("=" * 60)
    print("🎬 MovieMate - Database Initialization")
    print("=" * 60)
    print()

    # Step 1: Test connection
    print("📡 Step 1: Testing database connection...")

    if not test_connection():
        print("❌ Connection failed!")
        print()
        print("Troubleshooting:")
        print("1. Check if PostgreSQL is running")
        print("2. Verify DATABASE_URL in .env")
        print("3. Ensure database exists: createdb moviemate")
        print()
        return False

    print("✅ Connection successful!")
    print()

    # Step 2: Create tables
    print("📊 Step 2: Creating database tables...")

    try:
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created successfully!")
        print()

    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        print()
        return False

    # Step 3: Verify tables
    print("🔍 Step 3: Verifying tables...")

    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        if not tables:
            print("⚠️  No tables found!")
            return False

        print(f"✅ Found {len(tables)} tables:")
        print()

        for table_name in sorted(tables):
            columns = inspector.get_columns(table_name)
            indexes = inspector.get_indexes(table_name)

            print(f"   📊 {table_name}")
            print(f"      ├─ Columns: {len(columns)}")
            print(f"      └─ Indexes: {len(indexes)}")

        print()
        print("=" * 60)
        print("🎉 Database initialization completed!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Run: python run.py (to start the bot)")
        print()

        return True

    except Exception as e:
        print(f"❌ Error verifying tables: {e}")
        print()
        return False


if __name__ == "__main__":
    try:
        success = create_tables()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"❌ Unexpected error: {e}")
        sys.exit(1)