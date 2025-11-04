# database/connection.py
"""
Database Connection Management

Provides database connection utilities using SQLAlchemy.
"""

import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from sqlalchemy.exc import OperationalError

from config.settings import DATABASE_URL

logger = logging.getLogger(__name__)

# ENGINE

engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,
    echo=False,
    connect_args={
        "connect_timeout": 10,
        "options": "-c timezone=utc"
    }
)

logger.info("✅ Database engine created")

# SESSION FACTORY

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

logger.info("✅ Session factory created")

# SESSION CONTEXT MANAGER

@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions

    Automatically handles commit/rollback and cleanup.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
        logger.debug("✅ Session committed")
    except Exception as e:
        session.rollback()
        logger.error(f"❌ Session rolled back: {e}")
        raise
    finally:
        session.close()
        logger.debug("✅ Session closed")

# CONNECTION TEST

def test_connection() -> bool:
    """
    Test database connection

    Returns:
        bool: True if connected, False otherwise
    """
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            result.fetchone()

        logger.info("✅ Database connection successful")
        return True

    except OperationalError as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False

# CLEANUP

def dispose_engine():
    """Dispose database engine"""
    try:
        engine.dispose()
        logger.info("✅ Database engine disposed")
    except Exception as e:
        logger.error(f"❌ Error disposing engine: {e}")

