# database/models.py
"""
Database Models for MovieMateBot

SQLAlchemy ORM models for movie recommendation system.

Tables:
- users: User accounts
- user_preferences: User preferences (genres, ratings)
- favorites: Favorites movies
- watch_history: Watch history movies
- search_history: Search queries history
- recommendations_cache: Cached recommendations
- daily_stats: Daily statistics
"""

from datetime import datetime, date
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, Float,
    ForeignKey, Text, JSON, BigInteger, Index, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

# USER MODEL

class User(Base):
    """
    User account.

    Stores basic user information and settings.
    """
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Telegram info
    telegram_id = Column(
        BigInteger,
        unique=True,
        nullable=False,
        index=True,
        comment='Telegram user ID'
    )
    username = Column(String(255), nullable=False)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=True)

    # Settings
    language = Column(String(255), default='en', comment='Interface language')
    notifications_enabled = Column(Boolean, default=True)

    # Activity
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    last_active_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    preferences = relationship(
        "UserPreferences",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        lazy='joined'  # Eager load preferences with user
    )
    favorites = relationship('Favorite', back_populates='user', cascade='all, delete-orphan')
    watch_history = relationship("WatchHistory", back_populates='user', cascade='all, delete-orphan')
    search_history = relationship("SearchHistory", back_populates='user', cascade='all, delete-orphan')
    recommendations = relationship("RecommendationCache", back_populates='user', cascade='all, delete-orphan')

    # Indexes
    __table_args__ = (
        Index('idx_user_telegram_id', 'telegram_id'),
    )

    def __repr__(self):
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username='{self.username}')>"

# USER PREFERENCES MODEL

class UserPreferences(Base):
    """
    User preferences for movie recommendations

    Stores user's favorite genres, rating preferences, etc.
    """
    __tablename__ = 'user_preferences'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey('users.id', ondelete='CASCADE'),
        unique=True,
        nullable=False
    )

    # Genre preferences (array of genre IDs)
    # Example: [28, 12, 16] for Action, Adventure, Animation
    favorite_genres = Column(JSON, default=list, comment="List of favorite genre IDs")

    # Rating preferences
    min_rating = Column(Float, default=6.0, comment="Minimum rating (0-10)")

    # Year preferences
    preferred_year_from = Column(Integer, nullable=True, comment="From year (e.g., 2000)")
    preferred_year_to = Column(Integer, nullable=True, comment="To year (e.g., 2024)")

    # Language preferences
    preferred_languages = Column(JSON, default=list, comment="List of language codes")
    notifications_enabled = Column(Boolean, default=True)

    # Content preferences
    include_adult = Column(Boolean, default=False)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)



    # Relationship
    user = relationship("User", back_populates="preferences")

    def __repr__(self):
        return f"<UserPreferences(user_id={self.user_id}, min_rating={self.min_rating})>"

# FAVORITES MODEL

class Favorite(Base):
    """
    User's favorite movies/series

    Stores movies that user marked as favorite.
    """
    __tablename__ = 'favorites'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # TMDb data
    tmdb_id = Column(Integer, nullable=False, index=True, comment="TMDb movie/series ID")
    media_type = Column(String(20), default='movie', comment="movie or tv")

    # Cached data (to avoid extra API calls)
    title = Column(String(500), nullable=False)
    original_title = Column(String(500), nullable=True)
    poster_path = Column(String(500), nullable=True)
    backdrop_path = Column(String(500), nullable=True)
    overview = Column(Text, nullable=True)
    release_date = Column(String(20), nullable=True)
    vote_average = Column(Float, nullable=True)
    genres = Column(JSON, default=list, comment="List of genre names")

    added_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    user = relationship("User", back_populates="favorites")

    # Unique constraint: user can't favorite same movie twice
    __table_args__ = (
        UniqueConstraint('user_id', 'tmdb_id', name='uq_user_favorite'),
        Index('idx_favorite_user', 'user_id'),
        Index('idx_favorite_tmdb', 'tmdb_id'),
    )

    def __repr__(self):
        return f"<Favorite(user_id={self.user_id}, tmdb_id={self.tmdb_id}, title='{self.title}')>"

# WATCH HISTORY MODEL

class WatchHistory(Base):
    """
    User's watch history

    Tracks movies that user marked as watched.
    Used for recommendations.
    """
    __tablename__ = 'watch_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # TMDb data
    tmdb_id = Column(Integer, nullable=False, index=True)
    media_type = Column(String(20), default='movie')

    # Cached data
    title = Column(String(500), nullable=False)
    poster_path = Column(String(500), nullable=True)
    release_date = Column(String(20), nullable=True)
    genres = Column(JSON, default=list)

    # User rating (optional)
    user_rating = Column(Integer, nullable=True, comment="User's rating 1-10")

    watched_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    user = relationship("User", back_populates="watch_history")

    __table_args__ = (
        Index('idx_watch_user', 'user_id'),
        Index('idx_watch_tmdb', 'tmdb_id'),
        Index('idx_watch_date', 'watched_at'),
    )

    def __repr__(self):
        return f"<WatchHistory(user_id={self.user_id}, tmdb_id={self.tmdb_id}, title='{self.title}')>"

# SEARCH HISTORY MODEL

class SearchHistory(Base):
    """
    User's search queries history

    Tracks what users search for.
    Used for analytics and improving recommendations.
    """
    __tablename__ = 'search_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Search query
    query = Column(String(500), nullable=False, comment="Search text")
    search_type = Column(
        String(50),
        default='text',
        comment="text, genre, actor, year, etc."
    )

    # Applied filters (JSON)
    # Example: {"genre": "Action", "year": 2023, "min_rating": 7.0}
    filters = Column(JSON, default=dict, comment="Search filters")

    # Results
    results_count = Column(Integer, default=0, comment="Number of results found")

    searched_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    user = relationship("User", back_populates="search_history")

    __table_args__ = (
        Index('idx_search_user', 'user_id'),
        Index('idx_search_date', 'searched_at'),
        Index('idx_search_type', 'search_type'),
    )

    def __repr__(self):
        return f"<SearchHistory(user_id={self.user_id}, query='{self.query}')>"

# RECOMMENDATIONS CACHE MODEL

class RecommendationCache(Base):
    """
    Cached movie recommendations

    Stores pre-computed recommendations to reduce API calls.
    Has expiration time.
    """
    __tablename__ = 'recommendations_cache'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # TMDb data
    tmdb_id = Column(Integer, nullable=False)
    media_type = Column(String(20), default='movie')

    # Recommendation metadata
    score = Column(Float, nullable=False, comment="Recommendation score 0-100")
    reason = Column(String(500), nullable=True, comment="Why recommended")

    # Cached movie data
    title = Column(String(500), nullable=False)
    poster_path = Column(String(500), nullable=True)
    overview = Column(Text, nullable=True)
    vote_average = Column(Float, nullable=True)
    release_date = Column(String(20), nullable=True)
    genres = Column(JSON, default=list)

    # Cache management
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)

    # Relationship
    user = relationship("User", back_populates="recommendations")

    __table_args__ = (
        Index('idx_rec_user', 'user_id'),
        Index('idx_rec_expires', 'expires_at'),
        Index('idx_rec_score', 'score'),
    )

    def __repr__(self):
        return f"<RecommendationCache(user_id={self.user_id}, tmdb_id={self.tmdb_id}, score={self.score})>"

# DAILY STATS MODEL

class DailyStats(Base):
    """
    Daily aggregated statistics

    Stores daily metrics for analytics.
    Updated by background job.
    """
    __tablename__ = 'daily_stats'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Date
    date = Column(Date, unique=True, nullable=False, index=True)

    # User metrics
    total_users = Column(Integer, default=0)
    active_users = Column(Integer, default=0, comment="Users active today")
    new_users = Column(Integer, default=0, comment="New registrations")

    # Activity metrics
    total_searches = Column(Integer, default=0)
    total_favorites = Column(Integer, default=0, comment="Favorites added today")
    total_watched = Column(Integer, default=0, comment="Movies marked as watched")

    # Popular content (JSON)
    # Example: [{"tmdb_id": 123, "title": "Movie", "count": 45}, ...]
    top_movies = Column(JSON, default=list, comment="Most popular movies")
    top_genres = Column(JSON, default=list, comment="Most popular genres")
    top_searches = Column(JSON, default=list, comment="Most common searches")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_stats_date', 'date'),
    )

    def __repr__(self):
        return f"<DailyStats(date={self.date}, active_users={self.active_users})>"


