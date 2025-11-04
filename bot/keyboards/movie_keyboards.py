# bot/keyboards/movie_keyboards.py
"""
Movie-related Keyboards
"""

from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict, Any

# SEARCH RESULTS KEYBOARD

def get_search_results_keyboard(movies: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """
    Create keyboard with search results

    Args:
        movies: List of movie dictionaries

    Returns:
        Inline keyboard with movie buttons
    """
    keyboard = []

    for movie in movies[:10]:  # Max 10 results
        title = movie.get('title', 'Unknown')
        year = movie.get('year', '')
        tmdb_id = movie.get('tmdb_id', 0)
        rating = movie.get('vote_average', 0)

        # Button text with rating
        button_text = f"{title}"
        if year:
            button_text += f" ({year})"
        if rating > 0:
            button_text += f" ⭐{rating}"

        # Limit button text length
        if len(button_text) > 60:
            button_text = button_text[:57] + "..."

        keyboard.append([
            InlineKeyboardButton(
                button_text,
                callback_data=f"movie_{tmdb_id}"
            )
        ])

    # Back button
    keyboard.append([
        InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")
    ])

    return InlineKeyboardMarkup(keyboard)

# MOVIE DETAILS KEYBOARD

def get_movie_details_keyboard(
        tmdb_id: int,
        is_favorite: bool = False,
        is_watched: bool = False,
        show_trailer: bool = True
) -> InlineKeyboardMarkup:
    """
    Create keyboard for movie details

    Args:
        tmdb_id: TMDb movie ID
        is_favorite: Whether movie is in user's favorites
        is_watched: Whether movie is in user's watch history
        show_trailer: Whether to show trailer button

    Returns:
        Inline keyboard with action buttons
    """
    keyboard = []

    # Row 1: Favorite
    row1 = []

    if is_favorite:
        row1.append(
            InlineKeyboardButton("💔 Remove from Favorites", callback_data=f"unfav_{tmdb_id}")
        )
    else:
        row1.append(
            InlineKeyboardButton("❤️ Add to Favorites", callback_data=f"fav_{tmdb_id}")
        )

    keyboard.append(row1)

    # Row 2: Mark as Watched / Remove from Watched
    if is_watched:
        keyboard.append([
            InlineKeyboardButton("🗑️ Remove from Watched", callback_data=f"unwatched_{tmdb_id}")
        ])
    else:
        keyboard.append([
            InlineKeyboardButton("✅ Mark as Watched", callback_data=f"watched_{tmdb_id}")
        ])

    # Row 3: Recommendations
    keyboard.append([
        InlineKeyboardButton("🎯 Similar Movies", callback_data=f"similar_{tmdb_id}")
    ])

    # Row 4: Trailer (if available)
    if show_trailer:
        keyboard.append([
            InlineKeyboardButton("🎥 Watch Trailer", callback_data=f"trailer_{tmdb_id}")
        ])

    # Row 5: Navigation
    keyboard.append([
        InlineKeyboardButton("🔙 Back to Search", callback_data="back_search"),
        InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")
    ])

    return InlineKeyboardMarkup(keyboard)

# SIMPLE NAVIGATION KEYBOARD

def get_back_to_menu_keyboard() -> InlineKeyboardMarkup:
    """Simple back to menu button"""
    keyboard = [[
        InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")
    ]]

    return InlineKeyboardMarkup(keyboard)