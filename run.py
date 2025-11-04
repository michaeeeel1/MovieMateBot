# run.py
"""
MovieMate Bot - Main Entry Point

Entry point for the MovieMate Telegram bot.
"""

import sys
import logging
import signal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


# ============================================
# PRE-FLIGHT CHECKS
# ============================================

def validate_environment() -> bool:
    """Validate environment configuration"""
    logger.info("🔍 Step 1/3: Validating environment...")

    try:
        from config import settings

        # Check BOT_TOKEN
        if not settings.BOT_TOKEN:
            logger.error("❌ BOT_TOKEN is not set!")
            return False

        logger.info("✅ BOT_TOKEN: configured")

        # Check TMDB_API_KEY
        if not settings.TMDB_API_KEY:
            logger.error("❌ TMDB_API_KEY is not set!")
            return False

        logger.info("✅ TMDB_API_KEY: configured")

        # Check DATABASE_URL
        if not settings.DATABASE_URL:
            logger.error("❌ DATABASE_URL is not configured!")
            return False

        logger.info("✅ DATABASE_URL: configured")

        logger.info("✅ Environment validation passed\n")
        return True

    except Exception as e:
        logger.error(f"❌ Environment validation failed: {e}")
        return False


def check_database() -> bool:
    """Check database connection"""
    logger.info("🔍 Step 2/3: Checking database...")

    try:
        from database.connection import test_connection, engine
        from database.models import Base
        from sqlalchemy import inspect

        # Test connection
        if not test_connection():
            logger.error("❌ Cannot connect to database!")
            logger.error("   Run: python create_db.py")
            return False

        logger.info("✅ Database connection: OK")

        # Check tables
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        if not tables:
            logger.warning("⚠️  No tables found. Creating...")
            Base.metadata.create_all(bind=engine)
            logger.info("✅ Database tables created")
        else:
            logger.info(f"✅ Database tables: {len(tables)} found")

        logger.info("✅ Database check passed\n")
        return True

    except Exception as e:
        logger.error(f"❌ Database check failed: {e}")
        return False


def check_tmdb_api() -> bool:
    """Check TMDb API connection"""
    logger.info("🔍 Step 3/3: Checking TMDb API...")

    try:
        from bot.utils.tmdb_api import test_api_connection

        if not test_api_connection():
            logger.error("❌ TMDb API connection failed!")
            return False

        logger.info("✅ TMDb API connection: OK")
        logger.info("✅ TMDb API check passed\n")
        return True

    except Exception as e:
        logger.error(f"❌ TMDb API check failed: {e}")
        return False


def start_bot():
    """Start the bot"""
    logger.info("🤖 Starting MovieMate Bot...")

    try:
        from bot.main import main

        logger.info("=" * 60)
        logger.info("🎬 MovieMate Bot is running!")
        logger.info("=" * 60)

        main()

    except ImportError as e:
        logger.error(f"❌ Bot module not found: {e}")
        sys.exit(1)

    except KeyboardInterrupt:
        logger.info("\n⚠️  Bot stopped by user (Ctrl+C)")
        sys.exit(0)

    except Exception as e:
        logger.exception(f"❌ Bot crashed: {e}")
        sys.exit(1)


# ============================================
# SIGNAL HANDLERS
# ============================================

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info("\n⚠️  Received shutdown signal. Stopping bot...")
    sys.exit(0)


# Register signals
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


# ============================================
# MAIN
# ============================================

def main():
    """Main entry point"""
    print()
    print("=" * 60)
    print("🎬 MovieMate - Movie Recommendation Bot")
    print("=" * 60)
    print()

    # Pre-flight checks
    if not validate_environment():
        logger.error("❌ Environment check failed")
        sys.exit(1)

    if not check_database():
        logger.error("❌ Database check failed")
        sys.exit(1)

    if not check_tmdb_api():
        logger.error("❌ TMDb API check failed")
        sys.exit(1)

    # Start bot
    start_bot()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"💥 Fatal error: {e}")
        sys.exit(1)