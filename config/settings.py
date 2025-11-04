# config/settings.py
"""
Application Settings

Loads configuration from environment variables.
"""

import os
import logging
from typing import List
from dotenv import load_dotenv

load_dotenv()

# LOGGING

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%d-%b-%y %H:%M:%S'
)

logger = logging.getLogger(__name__)

# BOT CONFIGURATION

BOT_TOKEN = os.getenv('BOT_TOKEN')

if not BOT_TOKEN:
    logger.error('❌ BOT_TOKEN environment variable not set')
    raise ValueError('BOT_TOKEN environment variable not set')

logger.info("✅ Bot token loaded")

# TMDB API CONFIGURATION

TMDB_API_KEY = os.getenv('TMDB_API_KEY')

if not TMDB_API_KEY:
    logger.error("❌ TMDB_API_KEY not found in .env!")
    raise ValueError("TMDB_API_KEY is required")

logger.info("✅ TMDb API key loaded")

TMDB_API_VERSION = os.getenv('TMDB_API_VERSION', '3')

# DATABASE CONFIGURATION
DATABASE_URL = os.getenv('DATABASE_URL')

if DATABASE_URL:
    # Replace postgres:// with postgresql://
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    logger.info("✅ Using DATABASE_URL")
else:
    DB_USER = os.getenv('DB_USER', 'moviemate_user')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'secure_password_123')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'moviemate')

    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    logger.info(f"✅ Database: {DB_HOST}:{DB_PORT}/{DB_NAME}")

# ADMIN CONFIGURATION

ADMIN_IDS_STR = os.getenv('ADMIN_IDS', '')
ADMIN_IDS: List[int] = []

for id_str in ADMIN_IDS_STR.split(','):
    id_str = id_str.strip()
    if id_str.isdigit():
        ADMIN_IDS.append(int(id_str))

if ADMIN_IDS:
    logger.info(f"✅ Admin IDs: {ADMIN_IDS}")
else:
    logger.warning("⚠️  No admin IDs configured")

# BOT SETTINGS

LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
CACHE_DURATION = int(os.getenv('CACHE_DURATION', 3600))
MAX_SEARCH_RESULTS = int(os.getenv('MAX_SEARCH_RESULTS', 10))
RECOMMENDATIONS_COUNT = int(os.getenv('RECOMMENDATIONS_COUNT', 5))

logger.info(f"✅ Cache duration: {CACHE_DURATION}s")
logger.info(f"✅ Max search results: {MAX_SEARCH_RESULTS}")
logger.info(f"✅ Recommendations count: {RECOMMENDATIONS_COUNT}")

# SUMMARY

logger.info("="*60)
logger.info("📋 Configuration Summary:")
logger.info("="*60)
logger.info(f"Bot Token: {'✅ Set' if BOT_TOKEN else '❌ Missing'}")
logger.info(f"TMDb API Key: {'✅ Set' if TMDB_API_KEY else '❌ Missing'}")
logger.info(f"Database: {'✅ Configured' if DATABASE_URL else '❌ Missing'}")
logger.info(f"Admins: {len(ADMIN_IDS)} configured")
logger.info("="*60)
logger.info("✅ All settings loaded successfully!")
logger.info("="*60)


