# bot/utils/formatters.py
"""
Message Formatters

Utility functions for formatting messages.
"""

from typing import Dict, Any


def format_movie_card(movie: Dict[str, Any]) -> str:
    """
    Format movie data for Telegram message

    Args:
        movie: Movie dictionary from TMDb API

    Returns:
        Formatted text with movie info
    """
    title = movie.get('title', 'Unknown')
    year = movie.get('year', '')
    rating = movie.get('vote_average', 0)
    votes = movie.get('vote_count', 0)
    overview = movie.get('overview', 'No description available.')
    genres = movie.get('genres', [])

    # Truncate long overview
    if len(overview) > 300:
        overview = overview[:297] + '...'

    # Build message
    text = f"🎬 **{title}**"

    if year:
        text += f" ({year})"

    text += "\n\n"

    # Rating with stars
    if rating > 0:
        stars = "⭐" * int(rating / 2)
        text += f"{stars} **{rating}/10** ({votes:,} votes)\n"

    # Genres
    if genres:
        genres_text = ", ".join(genres[:3])  # Max 3 genres
        text += f"🎭 {genres_text}\n"

    text += f"\n{overview}"

    return text


def format_search_results_header(query: str, count: int) -> str:
    """Format search results header"""
    return (
        f"🔍 **Search Results for:** _{query}_\n\n"
        f"Found {count} movie(s). Tap to see details! 👇"
    )


def format_no_results(query: str) -> str:
    """Format no results message"""
    return (
        f"😕 **No Results Found**\n\n"
        f"Sorry, couldn't find any movies matching:\n"
        f"_{query}_\n\n"
        f"Try:\n"
        f"• Different spelling\n"
        f"• Original title\n"
        f"• Partial name\n"
        f"• Use 🔥 Trending to discover movies!"
    )