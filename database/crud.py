# database/crud.py
"""
CRUD Operations for MovieMate

Database operations for all models.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, desc

from database.models import (
    User, UserPreferences, Favorite, WatchHistory,
    SearchHistory, RecommendationCache, DailyStats
)

logger = logging.getLogger(__name__)

# USER CRUD

def get_user_by_telegram_id(session: Session, telegram_id: int) -> Optional[User]:
    """Get user by Telegram ID"""
    try:
        return session.query(User).filter(User.telegram_id == telegram_id).first()
    except Exception as e:
        logger.error(f"Error getting user {telegram_id}: {e}")
        return None


def create_user(
        session: Session,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
) -> Optional[User]:
    """Create new user"""
    try:
        # Check if user already exists first
        existing = get_user_by_telegram_id(session, telegram_id)
        if existing:
            logger.info(f"User {telegram_id} already exists, returning existing")
            return existing

        # Create new user
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            created_at=datetime.utcnow(),
            last_active_at=datetime.utcnow()
        )

        session.add(user)
        session.flush()  # Get user.id without committing yet

        # Create default preferences
        prefs = UserPreferences(
            user_id=user.id,
            favorite_genres=[],
            min_rating=6.0
        )
        session.add(prefs)

        # Commit everything together
        session.commit()
        session.refresh(user)

        logger.info(f"✅ Created new user: {telegram_id} ({username})")
        return user

    except Exception as e:
        session.rollback()
        logger.error(f"Error creating user: {e}")
        return None


def update_user_activity(session: Session, user_id: int) -> bool:
    """Update user's last activity timestamp"""
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            user.last_active_at = datetime.utcnow()
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        logger.error(f"Error updating activity: {e}")
        return False

# FAVORITES OPERATIONS

def add_to_favorites(
        session: Session,
        user_id: int,
        tmdb_id: int,
        media_type: str,
        title: str,
        **kwargs
) -> Optional[Favorite]:
    """Add movie to favorites"""
    try:
        favorite = Favorite(
            user_id=user_id,
            tmdb_id=tmdb_id,
            media_type=media_type,
            title=title,
            original_title=kwargs.get('original_title'),
            poster_path=kwargs.get('poster_path'),
            backdrop_path=kwargs.get('backdrop_path'),
            overview=kwargs.get('overview'),
            release_date=kwargs.get('release_date'),
            vote_average=kwargs.get('vote_average'),
            genres=kwargs.get('genres', []),
            added_at=datetime.utcnow()
        )

        session.add(favorite)
        session.commit()
        session.refresh(favorite)

        logger.info(f"✅ Added to favorites: {title}")
        return favorite

    except IntegrityError:
        session.rollback()
        logger.warning(f"Already in favorites: {tmdb_id}")
        return None

    except Exception as e:
        session.rollback()
        logger.error(f"Error adding favorite: {e}")
        return None


def remove_from_favorites(session: Session, user_id: int, tmdb_id: int) -> bool:
    """Remove from favorites"""
    try:
        favorite = session.query(Favorite).filter(
            Favorite.user_id == user_id,
            Favorite.tmdb_id == tmdb_id
        ).first()

        if favorite:
            session.delete(favorite)
            session.commit()
            logger.info(f"✅ Removed from favorites: {tmdb_id}")
            return True

        return False

    except Exception as e:
        session.rollback()
        logger.error(f"Error removing favorite: {e}")
        return False


def get_user_favorites(session: Session, user_id: int, limit: int = 50) -> List[Favorite]:
    """Get user's favorites"""
    try:
        return session.query(Favorite).filter(
            Favorite.user_id == user_id
        ).order_by(desc(Favorite.added_at)).limit(limit).all()
    except Exception as e:
        logger.error(f"Error getting favorites: {e}")
        return []


def is_in_favorites(session: Session, user_id: int, tmdb_id: int) -> bool:
    """Check if movie is in favorites"""
    try:
        exists = session.query(Favorite).filter(
            Favorite.user_id == user_id,
            Favorite.tmdb_id == tmdb_id
        ).first() is not None
        return exists
    except Exception as e:
        logger.error(f"Error checking favorite: {e}")
        return False

# SEARCH HISTORY OPERATIONS

def add_search_history(
        session: Session,
        user_id: int,
        query: str,
        search_type: str = 'text',
        filters: dict = None,
        results_count: int = 0
) -> Optional[SearchHistory]:
    """Add search to history"""
    try:
        search = SearchHistory(
            user_id=user_id,
            query=query,
            search_type=search_type,
            filters=filters or {},
            results_count=results_count,
            searched_at=datetime.utcnow()
        )

        session.add(search)
        session.commit()

        return search

    except Exception as e:
        session.rollback()
        logger.error(f"Error adding search history: {e}")
        return None


def get_user_search_history(session: Session, user_id: int, limit: int = 20) -> List[SearchHistory]:
    """Get user's search history"""
    try:
        return session.query(SearchHistory).filter(
            SearchHistory.user_id == user_id
        ).order_by(desc(SearchHistory.searched_at)).limit(limit).all()
    except Exception as e:
        logger.error(f"Error getting search history: {e}")
        return []

# STATISTICS

def get_user_stats(session: Session, user_id: int) -> dict:
    """Get user statistics"""
    try:
        favorites_count = session.query(Favorite).filter(
            Favorite.user_id == user_id
        ).count()

        watched_count = session.query(WatchHistory).filter(
            WatchHistory.user_id == user_id
        ).count()

        searches_count = session.query(SearchHistory).filter(
            SearchHistory.user_id == user_id
        ).count()

        return {
            'favorites': favorites_count,
            'watched': watched_count,
            'searches': searches_count
        }

    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return {'favorites': 0, 'watched': 0, 'searches': 0}

