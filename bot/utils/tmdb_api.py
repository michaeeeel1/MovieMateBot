# bot/utils/tmdb_api.py
"""
TMDb API Wrapper

Provides convenient functions to interact with The Movie Database API.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from tmdbv3api import TMDb, Movie, TV, Genre, Trending, Discover
import requests

from config.settings import TMDB_API_KEY

logger = logging.getLogger(__name__)

# TMDB CONFIGURATION

tmdb = TMDb()
tmdb.api_key = TMDB_API_KEY
tmdb.language = 'en-US'  # Default language

# Initialize API objects
movie_api = Movie()
tv_api = TV()
genre_api = Genre()
trending_api = Trending()
discover_api = Discover()

logger.info("✅ TMDb API initialized")

# CONSTANTS

POSTER_BASE_URL = "https://image.tmdb.org/t/p/w500"
BACKDROP_BASE_URL = "https://image.tmdb.org/t/p/original"

# HELPER FUNCTIONS

def get_poster_url(poster_path: Optional[str]) -> Optional[str]:
    """Get full poster URL"""
    if poster_path:
        return f"{POSTER_BASE_URL}{poster_path}"
    return None


def get_backdrop_url(backdrop_path: Optional[str]) -> Optional[str]:
    """Get full backdrop URL"""
    if backdrop_path:
        return f"{BACKDROP_BASE_URL}{backdrop_path}"
    return None


def format_movie_data(movie: Any, media_type: str = 'movie') -> Dict[str, Any]:
    """
    Format movie/TV data to consistent structure

    Args:
        movie: Movie or TV object from TMDb
        media_type: 'movie' or 'tv'

    Returns:
        Formatted dictionary with movie data
    """
    try:
        # Helper function to safely get attribute
        def safe_get(obj, attr, default=''):
            try:
                # Try as dict first
                if isinstance(obj, dict):
                    value = obj.get(attr, default)
                else:
                    # Try as object attribute
                    value = getattr(obj, attr, default)

                # If it's a method, return default
                if callable(value):
                    return default

                return value if value is not None else default
            except:
                return default

        # Get title (different field for movies vs TV)
        if media_type == 'tv':
            title = safe_get(movie, 'name', 'Unknown')
            original_title = safe_get(movie, 'original_name', title)
            release_date = safe_get(movie, 'first_air_date', '')
        else:
            title = safe_get(movie, 'title', 'Unknown')
            original_title = safe_get(movie, 'original_title', title)
            release_date = safe_get(movie, 'release_date', '')

        # Ensure title is not empty
        if not title or title == 'Unknown':
            title = safe_get(movie, 'original_title', 'Unknown Movie')

        # Extract year from release date
        year = ''
        if release_date and isinstance(release_date, str) and len(release_date) >= 4:
            try:
                year = int(release_date[:4])
            except:
                year = ''

        # Get genre IDs
        genre_ids = safe_get(movie, 'genre_ids', [])
        if not isinstance(genre_ids, list):
            genre_ids = []

        # Get genre names if available
        genres = []
        if genre_ids:
            genres = get_genre_names(genre_ids, media_type)

        # Get poster and backdrop paths
        poster_path = safe_get(movie, 'poster_path', None)
        backdrop_path = safe_get(movie, 'backdrop_path', None)

        # Get vote average and count
        vote_average = safe_get(movie, 'vote_average', 0)
        try:
            vote_average = round(float(vote_average), 1) if vote_average else 0.0
        except:
            vote_average = 0.0

        vote_count = safe_get(movie, 'vote_count', 0)
        try:
            vote_count = int(vote_count) if vote_count else 0
        except:
            vote_count = 0

        # Get popularity
        popularity = safe_get(movie, 'popularity', 0)
        try:
            popularity = float(popularity) if popularity else 0
        except:
            popularity = 0

        # Get TMDb ID
        tmdb_id = safe_get(movie, 'id', 0)
        try:
            tmdb_id = int(tmdb_id) if tmdb_id else 0
        except:
            tmdb_id = 0

        return {
            'tmdb_id': tmdb_id,
            'media_type': media_type,
            'title': str(title),
            'original_title': str(original_title),
            'overview': str(safe_get(movie, 'overview', '')),
            'poster_path': poster_path,
            'backdrop_path': backdrop_path,
            'poster_url': get_poster_url(poster_path),
            'backdrop_url': get_backdrop_url(backdrop_path),
            'release_date': str(release_date),
            'year': year,
            'vote_average': vote_average,
            'vote_count': vote_count,
            'popularity': popularity,
            'genre_ids': genre_ids,
            'genres': genres,
            'adult': safe_get(movie, 'adult', False)
        }

    except Exception as e:
        logger.error(f"Error formatting movie data: {e}")
        logger.error(f"Movie object: {movie}")
        return {}

# GENRE OPERATIONS

# Cache for genres (avoid repeated API calls)
_genre_cache = {'movie': {}, 'tv': {}}


def get_all_genres(media_type: str = 'movie') -> Dict[int, str]:
    """
    Get all genres for media type

    Args:
        media_type: 'movie' or 'tv'

    Returns:
        Dictionary {genre_id: genre_name}
    """
    global _genre_cache

    # Return from cache if available
    if _genre_cache[media_type]:
        return _genre_cache[media_type]

    try:
        if media_type == 'movie':
            genres = genre_api.movie_list()
        else:
            genres = genre_api.tv_list()

        genre_dict = {g.id: g.name for g in genres}
        _genre_cache[media_type] = genre_dict

        logger.info(f"✅ Loaded {len(genre_dict)} {media_type} genres")
        return genre_dict

    except Exception as e:
        logger.error(f"Error getting genres: {e}")
        return {}


def get_genre_names(genre_ids: List[int], media_type: str = 'movie') -> List[str]:
    """
    Convert genre IDs to names

    Args:
        genre_ids: List of genre IDs
        media_type: 'movie' or 'tv'

    Returns:
        List of genre names
    """
    genres_dict = get_all_genres(media_type)
    return [genres_dict.get(gid, 'Unknown') for gid in genre_ids]

# SEARCH OPERATIONS

def search_movies(query: str, page: int = 1, year: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Search for movies by title

    Args:
        query: Search query
        page: Page number (default: 1)
        year: Filter by year (optional, filters results after search)

    Returns:
        List of movie dictionaries
    """
    try:
        logger.info(f"Searching movies: '{query}' (page {page})")

        # Search without year parameter (not supported by library)
        results = movie_api.search(query, page=page)

        # Format movies
        movies = [format_movie_data(m, 'movie') for m in results]

        # Filter by year if specified (client-side filtering)
        if year:
            movies = [m for m in movies if m.get('year') == year]

        # Limit to 10
        movies = movies[:10]

        logger.info(f"✅ Found {len(movies)} movies")
        return movies

    except Exception as e:
        logger.error(f"Error searching movies: {e}")
        return []


def search_tv(query: str, page: int = 1) -> List[Dict[str, Any]]:
    """
    Search for TV series by title

    Args:
        query: Search query
        page: Page number

    Returns:
        List of TV series dictionaries
    """
    try:
        logger.info(f"Searching TV series: '{query}' (page {page})")

        results = tv_api.search(query, page=page)

        # Convert to list first
        series = []
        for s in results:
            formatted = format_movie_data(s, 'tv')
            if formatted:
                series.append(formatted)
            if len(series) >= 10:
                break

        logger.info(f"✅ Found {len(series)} TV series")
        return series

    except Exception as e:
        logger.error(f"Error searching TV series: {e}")
        return []

# MOVIE DETAILS

def get_movie_details(movie_id: int) -> Optional[Dict[str, Any]]:
    """
    Get detailed information about a movie

    Args:
        movie_id: TMDb movie ID

    Returns:
        Movie details dictionary
    """
    try:
        logger.info(f"Getting movie details: {movie_id}")

        movie = movie_api.details(movie_id)

        # Format basic data
        data = format_movie_data(movie, 'movie')

        # Add additional details
        data.update({
            'runtime': getattr(movie, 'runtime', 0),
            'budget': getattr(movie, 'budget', 0),
            'revenue': getattr(movie, 'revenue', 0),
            'tagline': getattr(movie, 'tagline', ''),
            'status': getattr(movie, 'status', ''),
            'homepage': getattr(movie, 'homepage', ''),
            'imdb_id': getattr(movie, 'imdb_id', ''),
        })

        # Get production countries
        countries = getattr(movie, 'production_countries', [])
        data['countries'] = [c.name for c in countries] if countries else []

        # Get spoken languages
        languages = getattr(movie, 'spoken_languages', [])
        data['languages'] = [l.name for l in languages] if languages else []

        logger.info(f"✅ Got details for: {data['title']}")
        return data

    except Exception as e:
        logger.error(f"Error getting movie details: {e}")
        return None

# POPULAR & TRENDING

def get_popular_movies(page: int = 1) -> List[Dict[str, Any]]:
    """
    Get popular movies

    Args:
        page: Page number

    Returns:
        List of popular movies
    """
    try:
        logger.info(f"Getting popular movies (page {page})")

        results = movie_api.popular(page=page)

        # Convert to list first, then format
        movies = []
        for m in results:
            formatted = format_movie_data(m, 'movie')
            if formatted:
                movies.append(formatted)
            if len(movies) >= 10:  # Limit to 10
                break

        logger.info(f"✅ Got {len(movies)} popular movies")
        return movies

    except Exception as e:
        logger.error(f"Error getting popular movies: {e}")
        return []


def get_trending(media_type: str = 'movie', time_window: str = 'week') -> List[Dict[str, Any]]:
    """
    Get trending movies/TV series

    Args:
        media_type: 'movie' or 'tv'
        time_window: 'day' or 'week'

    Returns:
        List of trending items
    """
    try:
        logger.info(f"Getting trending {media_type} ({time_window})")

        # Use correct method based on media type and time window
        if media_type == 'movie':
            if time_window == 'day':
                results = trending_api.movie_day()
            else:
                results = trending_api.movie_week()
        else:  # tv
            if time_window == 'day':
                results = trending_api.tv_day()
            else:
                results = trending_api.tv_week()

        # Convert to list first
        items = []
        for item in results:
            formatted = format_movie_data(item, media_type)
            if formatted:
                items.append(formatted)
            if len(items) >= 10:
                break

        logger.info(f"✅ Got {len(items)} trending {media_type}")
        return items

    except Exception as e:
        logger.error(f"Error getting trending: {e}")
        return []

# DISCOVER (FILTERS)

def discover_movies(
        genre_ids: Optional[List[int]] = None,
        min_rating: float = 0.0,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        sort_by: str = 'popularity.desc',
        page: int = 1
) -> List[Dict[str, Any]]:
    """
    Discover movies with filters

    Args:
        genre_ids: List of genre IDs
        min_rating: Minimum vote average
        year_from: Start year
        year_to: End year
        sort_by: Sort method
        page: Page number

    Returns:
        List of movies
    """
    try:
        logger.info(f"Discovering movies: genres={genre_ids}, rating={min_rating}, years={year_from}-{year_to}")

        # Use Discover API correctly
        from tmdbv3api import Discover
        discover_api = Discover()

        # Build discover parameters as dict
        discover_params = {}

        if genre_ids:
            discover_params['with_genres'] = '|'.join(map(str, genre_ids))  # OR operation

        if min_rating > 0:
            discover_params['vote_average.gte'] = min_rating
            discover_params['vote_count.gte'] = 100

        if year_from:
            discover_params['primary_release_date.gte'] = f"{year_from}-01-01"

        if year_to:
            discover_params['primary_release_date.lte'] = f"{year_to}-12-31"

        discover_params['sort_by'] = sort_by

        # Make API call - discover_movies() returns list directly
        results = discover_api.discover_movies(discover_params)

        if not results:
            logger.warning("No results from discover")
            return []

        movies = []
        for movie in results:
            formatted = format_movie_data(movie, 'movie')
            if formatted and formatted.get('tmdb_id'):
                movies.append(formatted)

            if len(movies) >= 20:
                break

        logger.info(f"✅ Discovered {len(movies)} movies")
        return movies

    except Exception as e:
        logger.error(f"Error discovering movies: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return []

# RECOMMENDATIONS

def get_movie_recommendations(movie_id: int, page: int = 1) -> List[Dict[str, Any]]:
    """
    Get TMDb recommendations for a movie

    Args:
        movie_id: TMDb movie ID
        page: Page number

    Returns:
        List of recommended movies
    """
    try:
        logger.info(f"Getting recommendations for movie {movie_id}")

        results = movie_api.recommendations(movie_id=movie_id, page=page)

        # Convert to list first
        movies = []
        for m in results:
            formatted = format_movie_data(m, 'movie')
            if formatted:
                movies.append(formatted)
            if len(movies) >= 10:
                break

        logger.info(f"✅ Got {len(movies)} recommendations")
        return movies

    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        return []

# UTILITY FUNCTIONS

def get_movie_trailer_url(movie_id: int) -> Optional[str]:
    """
    Get YouTube trailer URL for movie

    Args:
        movie_id: TMDb movie ID

    Returns:
        YouTube URL or None
    """
    try:
        videos = movie_api.videos(movie_id)

        # Find first YouTube trailer
        for video in videos:
            if video.site == 'YouTube' and video.type == 'Trailer':
                return f"https://www.youtube.com/watch?v={video.key}"

        return None

    except Exception as e:
        logger.error(f"Error getting trailer: {e}")
        return None


def format_movie_card(movie: Dict[str, Any]) -> str:
    """
    Format movie data for display in Telegram

    Args:
        movie: Movie dictionary

    Returns:
        Formatted text
    """
    title = movie.get('title', 'Unknown')
    year = movie.get('year', '')
    rating = movie.get('vote_average', 0)
    overview = movie.get('overview', 'No description available.')
    genres = ', '.join(movie.get('genres', []))

    # Truncate overview if too long
    if len(overview) > 300:
        overview = overview[:297] + '...'

    text = f"🎬 **{title}**"

    if year:
        text += f" ({year})"

    text += f"\n\n⭐ Rating: {rating}/10"

    if genres:
        text += f"\n🎭 Genres: {genres}"

    text += f"\n\n{overview}"

    return text

# INITIALIZATION CHECK

def test_api_connection() -> bool:
    """
    Test TMDb API connection

    Returns:
        True if API is working, False otherwise
    """
    try:
        # Try to get popular movies
        results = movie_api.popular(page=1)

        if results:
            logger.info("✅ TMDb API connection successful")
            return True

        logger.error("❌ TMDb API returned no results")
        return False

    except Exception as e:
        logger.error(f"❌ TMDb API connection failed: {e}")
        return False


# Test connection on import
if test_api_connection():
    logger.info("✅ TMDb API wrapper ready")
else:
    logger.warning("⚠️  TMDb API connection issues detected")


# ============================================
# TV SHOWS API
# ============================================

def search_tv_shows(query: str, page: int = 1) -> List[Dict[str, Any]]:
    """
    Search for TV shows

    Args:
        query: Search query
        page: Page number

    Returns:
        List of TV shows
    """
    try:
        logger.info(f"Searching TV shows: '{query}'")

        from tmdbv3api import TV
        tv_api = TV()

        results = tv_api.search(query)

        if not results:
            logger.warning(f"No TV shows found for: {query}")
            return []

        shows = []
        for show in results[:20]:
            formatted = format_movie_data(show, 'tv')
            if formatted and formatted.get('tmdb_id'):
                shows.append(formatted)

        logger.info(f"✅ Found {len(shows)} TV shows")
        return shows

    except Exception as e:
        logger.error(f"Error searching TV shows: {e}")
        return []


def get_tv_show_details(tv_id: int) -> Optional[Dict[str, Any]]:
    """
    Get detailed TV show information

    Args:
        tv_id: TMDb TV show ID

    Returns:
        TV show details dictionary
    """
    try:
        logger.info(f"Getting TV show details for ID: {tv_id}")

        from tmdbv3api import TV
        tv_api = TV()

        show = tv_api.details(tv_id)

        if not show:
            logger.warning(f"TV show not found: {tv_id}")
            return None

        # Format basic data
        formatted = format_movie_data(show, 'tv')

        if not formatted:
            return None

        # Add TV-specific details
        formatted['number_of_seasons'] = safe_get(show, 'number_of_seasons', 0)
        formatted['number_of_episodes'] = safe_get(show, 'number_of_episodes', 0)
        formatted['status'] = safe_get(show, 'status', 'Unknown')
        formatted['type'] = safe_get(show, 'type', 'Scripted')
        formatted['first_air_date'] = safe_get(show, 'first_air_date', '')
        formatted['last_air_date'] = safe_get(show, 'last_air_date', '')
        formatted['in_production'] = safe_get(show, 'in_production', False)

        # Get networks
        networks = safe_get(show, 'networks', [])
        formatted['networks'] = [safe_get(n, 'name', '') for n in networks] if networks else []

        # Get seasons info
        seasons = safe_get(show, 'seasons', [])
        formatted['seasons'] = []
        if seasons:
            for season in seasons:
                formatted['seasons'].append({
                    'season_number': safe_get(season, 'season_number', 0),
                    'name': safe_get(season, 'name', ''),
                    'episode_count': safe_get(season, 'episode_count', 0),
                    'air_date': safe_get(season, 'air_date', '')
                })

        logger.info(f"✅ Got TV show details: {formatted['title']}")
        return formatted

    except Exception as e:
        logger.error(f"Error getting TV show details: {e}")
        return None


def get_trending_tv(time_window: str = 'week') -> List[Dict[str, Any]]:
    """
    Get trending TV shows

    Args:
        time_window: 'day' or 'week'

    Returns:
        List of trending TV shows
    """
    try:
        logger.info(f"Getting trending TV shows ({time_window})")

        results = trending_api.tv_week() if time_window == 'week' else trending_api.tv_day()

        if not results:
            logger.warning("No trending TV shows found")
            return []

        shows = []
        for show in results[:20]:
            formatted = format_movie_data(show, 'tv')
            if formatted and formatted.get('tmdb_id'):
                shows.append(formatted)

        logger.info(f"✅ Found {len(shows)} trending TV shows")
        return shows

    except Exception as e:
        logger.error(f"Error getting trending TV: {e}")
        return []


def get_popular_tv_shows(page: int = 1) -> List[Dict[str, Any]]:
    """
    Get popular TV shows

    Args:
        page: Page number

    Returns:
        List of popular TV shows
    """
    try:
        logger.info("Getting popular TV shows")

        from tmdbv3api import TV
        tv_api = TV()

        results = tv_api.popular()

        if not results:
            logger.warning("No popular TV shows found")
            return []

        shows = []
        for show in results[:20]:
            formatted = format_movie_data(show, 'tv')
            if formatted and formatted.get('tmdb_id'):
                shows.append(formatted)

        logger.info(f"✅ Found {len(shows)} popular TV shows")
        return shows

    except Exception as e:
        logger.error(f"Error getting popular TV: {e}")
        return []


def get_tv_recommendations(tv_id: int, page: int = 1) -> List[Dict[str, Any]]:
    """
    Get TV show recommendations

    Args:
        tv_id: TMDb TV show ID
        page: Page number

    Returns:
        List of similar TV shows
    """
    try:
        logger.info(f"Getting recommendations for TV show {tv_id}")

        from tmdbv3api import TV
        tv_api = TV()

        results = tv_api.recommendations(tv_id)

        if not results:
            # Fallback to similar
            results = tv_api.similar(tv_id)

        if not results:
            logger.warning(f"No recommendations for TV show {tv_id}")
            return []

        shows = []
        for show in results[:20]:
            formatted = format_movie_data(show, 'tv')
            if formatted and formatted.get('tmdb_id'):
                shows.append(formatted)

        logger.info(f"✅ Found {len(shows)} TV recommendations")
        return shows

    except Exception as e:
        logger.error(f"Error getting TV recommendations: {e}")
        return []


def discover_tv_shows(
        genre_ids: Optional[List[int]] = None,
        min_rating: float = 0.0,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        sort_by: str = 'popularity.desc',
        page: int = 1
) -> List[Dict[str, Any]]:
    """
    Discover TV shows with filters

    Args:
        genre_ids: List of genre IDs
        min_rating: Minimum vote average
        year_from: Start year
        year_to: End year
        sort_by: Sort method
        page: Page number

    Returns:
        List of TV shows
    """
    try:
        logger.info(f"Discovering TV shows: genres={genre_ids}, rating={min_rating}, years={year_from}-{year_to}")

        from tmdbv3api import Discover
        discover_api = Discover()

        discover_params = {}

        if genre_ids:
            discover_params['with_genres'] = '|'.join(map(str, genre_ids))

        if min_rating > 0:
            discover_params['vote_average.gte'] = min_rating
            discover_params['vote_count.gte'] = 50  # Lower threshold for TV

        if year_from:
            discover_params['first_air_date.gte'] = f"{year_from}-01-01"

        if year_to:
            discover_params['first_air_date.lte'] = f"{year_to}-12-31"

        discover_params['sort_by'] = sort_by

        results = discover_api.discover_tv_shows(discover_params)

        if not results:
            logger.warning("No TV shows from discover")
            return []

        shows = []
        for show in results:
            formatted = format_movie_data(show, 'tv')
            if formatted and formatted.get('tmdb_id'):
                shows.append(formatted)

            if len(shows) >= 20:
                break

        logger.info(f"✅ Discovered {len(shows)} TV shows")
        return shows

    except Exception as e:
        logger.error(f"Error discovering TV shows: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return []


def get_tv_trailer_url(tv_id: int) -> Optional[str]:
    """
    Get TV show trailer URL from YouTube

    Args:
        tv_id: TMDb TV show ID

    Returns:
        YouTube URL or None
    """
    try:
        from tmdbv3api import TV
        tv_api = TV()

        videos = tv_api.videos(tv_id)

        if not videos:
            return None

        # Find trailer
        for video in videos:
            if video.get('type') == 'Trailer' and video.get('site') == 'YouTube':
                key = video.get('key')
                if key:
                    return f"https://www.youtube.com/watch?v={key}"

        # Fallback to any YouTube video
        for video in videos:
            if video.get('site') == 'YouTube':
                key = video.get('key')
                if key:
                    return f"https://www.youtube.com/watch?v={key}"

        return None

    except Exception as e:
        logger.error(f"Error getting TV trailer: {e}")
        return None

