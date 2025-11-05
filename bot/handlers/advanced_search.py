# bot/handlers/advanced_search.py
"""
Advanced Search Handler

Search with filters (genre, year, rating).
"""

import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from bot.utils.tmdb_api import discover_movies, get_all_genres
from bot.keyboards.movie_keyboards import get_search_results_keyboard, get_back_to_menu_keyboard
from bot.utils.formatters import format_search_results_header

logger = logging.getLogger(__name__)

# Genre emoji mapping
GENRE_EMOJI = {
    'Action': '💥',
    'Adventure': '🗺️',
    'Animation': '🎨',
    'Comedy': '😂',
    'Crime': '🔫',
    'Documentary': '📹',
    'Drama': '🎭',
    'Family': '👨‍👩‍👧',
    'Fantasy': '🧙',
    'History': '📜',
    'Horror': '👻',
    'Music': '🎵',
    'Mystery': '🔍',
    'Romance': '💕',
    'Science Fiction': '🚀',
    'TV Movie': '📺',
    'Thriller': '😱',
    'War': '⚔️',
    'Western': '🤠'
}

# START ADVANCED SEARCH

async def start_advanced_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Start advanced search flow

    Show filter options.
    """
    logger.info(f"User {update.effective_user.id} started advanced search")

    # Initialize search filters in context
    if 'search_filters' not in context.user_data:
        context.user_data['search_filters'] = {
            'genres': [],
            'year_from': None,
            'year_to': None,
            'min_rating': 6.0
        }

    await show_filter_menu(update, context)

# SHOW FILTER MENU

async def show_filter_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, edit: bool = False) -> None:
    """Show advanced search filter menu"""
    filters = context.user_data.get('search_filters', {})

    genres = filters.get('genres', [])
    year_from = filters.get('year_from', 'Any')
    year_to = filters.get('year_to', 'Any')
    min_rating = filters.get('min_rating', 6.0)

    # Format current filters
    genre_text = f"{len(genres)} selected" if genres else "Any"
    year_text = f"{year_from}-{year_to}" if year_from and year_to else "Any"

    filter_text = (
        f"🔍 **Advanced Search**\n\n"
        f"**Current Filters:**\n"
        f"🎭 Genre: {genre_text}\n"
        f"📅 Year: {year_text}\n"
        f"⭐ Min Rating: {min_rating}/10\n\n"
        f"Select filters and tap Search when ready:"
    )

    keyboard = [
        [
            InlineKeyboardButton("🎭 Select Genres", callback_data="adv_search_genre")
        ],
        [
            InlineKeyboardButton("📅 Select Year Range", callback_data="adv_search_year")
        ],
        [
            InlineKeyboardButton("⭐ Min Rating", callback_data="adv_search_rating")
        ],
        [
            InlineKeyboardButton("🔍 Search Now", callback_data="adv_search_execute")
        ],
        [
            InlineKeyboardButton("🔄 Reset Filters", callback_data="adv_search_reset"),
            InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")
        ]
    ]

    if edit:
        query = update.callback_query
        await query.edit_message_text(
            filter_text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text(
            filter_text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# GENRE SELECTION

async def show_genre_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show genre selection menu"""
    query = update.callback_query
    await query.answer()

    # Get all genres
    genres = get_all_genres('movie')

    if not genres:
        await query.answer("❌ Could not load genres", show_alert=True)
        return

    # Get currently selected genre NAMES (not IDs!)
    selected_names = context.user_data.get('search_filters', {}).get('genres', [])

    # Create keyboard with checkboxes
    keyboard = []

    for genre_name, genre_id in sorted(genres.items()):
        emoji = GENRE_EMOJI.get(genre_name, '🎬')
        # Check if THIS genre name is in selected list
        checkbox = '✅' if genre_name in selected_names else '☐'

        keyboard.append([
            InlineKeyboardButton(
                f"{checkbox} {emoji} {genre_name}",  # ← ПОКАЗЫВАЕМ НАЗВАНИЕ!
                callback_data=f"toggle_genre_{genre_name}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton("✔️ Done", callback_data="genre_done"),
        InlineKeyboardButton("❌ Clear All", callback_data="genre_clear")
    ])

    await query.edit_message_text(
        f"🎭 **Select Genres**\n\n"
        f"Selected: {len(selected_names)}\n"
        f"Tap to toggle:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def toggle_genre(update: Update, context: ContextTypes.DEFAULT_TYPE, genre_name: str) -> None:
    """Toggle genre selection"""
    query = update.callback_query
    await query.answer()

    # Get current selection
    filters = context.user_data.get('search_filters', {})
    selected = filters.get('genres', [])

    # Toggle
    if genre_name in selected:
        selected.remove(genre_name)
    else:
        selected.append(genre_name)

    # Update context
    filters['genres'] = selected
    context.user_data['search_filters'] = filters

    # Refresh menu
    await show_genre_selection(update, context)

# YEAR RANGE SELECTION

async def show_year_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show year range selection"""
    query = update.callback_query
    await query.answer()

    current_year = 2025

    keyboard = []

    # Predefined ranges
    ranges = [
        ("2024-2025", 2024, 2025),
        ("2020-2024", 2020, 2024),
        ("2015-2020", 2015, 2020),
        ("2010-2015", 2010, 2015),
        ("2000-2010", 2000, 2010),
        ("1990-2000", 1990, 2000),
        ("1980-1990", 1980, 1990),
        ("Before 1980", 1900, 1980),
    ]

    for label, year_from, year_to in ranges:
        keyboard.append([
            InlineKeyboardButton(
                f"📅 {label}",
                callback_data=f"year_range_{year_from}_{year_to}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton("✔️ Done", callback_data="year_done")
    ])

    await query.edit_message_text(
        "📅 **Select Year Range**\n\n"
        "Choose a time period:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def set_year_range(update: Update, context: ContextTypes.DEFAULT_TYPE, year_from: int, year_to: int) -> None:
    """Set year range"""
    query = update.callback_query
    await query.answer()

    # Update filters
    filters = context.user_data.get('search_filters', {})
    filters['year_from'] = year_from
    filters['year_to'] = year_to
    context.user_data['search_filters'] = filters

    await query.answer(f"📅 Year range: {year_from}-{year_to}", show_alert=True)

    # Back to main menu
    await show_filter_menu(update, context, edit=True)

# RATING SELECTION

async def show_rating_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show rating selection"""
    query = update.callback_query
    await query.answer()

    keyboard = []

    for rating in [5.0, 6.0, 7.0, 7.5, 8.0, 8.5, 9.0]:
        keyboard.append([
            InlineKeyboardButton(
                f"⭐ {rating}+",
                callback_data=f"adv_rating_{rating}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton("✔️ Done", callback_data="rating_done")
    ])

    await query.edit_message_text(
        "⭐ **Select Minimum Rating**\n\n"
        "Movies must have at least this rating:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def set_rating(update: Update, context: ContextTypes.DEFAULT_TYPE, rating: float) -> None:
    """Set minimum rating"""
    query = update.callback_query
    await query.answer()

    # Update filters
    filters = context.user_data.get('search_filters', {})
    filters['min_rating'] = rating
    context.user_data['search_filters'] = filters

    await query.answer(f"⭐ Min rating: {rating}+", show_alert=True)

    # Back to main menu
    await show_filter_menu(update, context, edit=True)

# EXECUTE SEARCH

async def execute_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Execute advanced search with filters"""
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    filters = context.user_data.get('search_filters', {})

    logger.info(f"User {user.id} executing advanced search with filters: {filters}")

    # Show loading
    await query.edit_message_text(
        "🔍 Searching with your filters...",
        parse_mode='Markdown'
    )

    # Get genre IDs
    genre_ids = []
    if filters.get('genres'):
        all_genres = get_all_genres('movie')
        genre_ids = [all_genres[g] for g in filters['genres'] if g in all_genres]

    # Build discover parameters
    kwargs = {
        'min_rating': filters.get('min_rating', 6.0),
        'sort_by': 'popularity.desc',
        'page': 1
    }

    if genre_ids:
        kwargs['genre_ids'] = genre_ids

    if filters.get('year_from') and filters.get('year_to'):
        kwargs['year_from'] = filters['year_from']
        kwargs['year_to'] = filters['year_to']

    # Execute search
    results = discover_movies(**kwargs)

    if not results or len(results) == 0:
        await query.edit_message_text(
            "😕 **No Results**\n\n"
            "No movies match your filters.\n"
            "Try adjusting your criteria!",
            parse_mode='Markdown',
            reply_markup=get_back_to_menu_keyboard()
        )
        return

    # Format filters for display
    filter_parts = []
    if filters.get('genres'):
        filter_parts.append(f"Genres: {', '.join(filters['genres'][:3])}")
    if filters.get('year_from'):
        filter_parts.append(f"Years: {filters['year_from']}-{filters['year_to']}")
    filter_parts.append(f"Rating: {filters['min_rating']}+")

    filter_text = " | ".join(filter_parts)

    header = (
        f"🔍 **Advanced Search Results**\n\n"
        f"Filters: {filter_text}\n"
        f"Found {len(results)} movies! 🎬\n"
        f"Tap to see details 👇"
    )

    # Store results
    context.user_data['last_search_results'] = results
    context.user_data['last_search_query'] = 'advanced search'

    # Show results
    keyboard = get_search_results_keyboard(results)

    await query.edit_message_text(
        header,
        parse_mode='Markdown',
        reply_markup=keyboard
    )

    logger.info(f"Advanced search returned {len(results)} results")

# RESET FILTERS

async def reset_filters(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reset all filters to default"""
    query = update.callback_query

    # Check if already default
    current_filters = context.user_data.get('search_filters', {})

    if (not current_filters.get('genres') and
            not current_filters.get('year_from') and
            not current_filters.get('year_to') and
            current_filters.get('min_rating', 6.0) == 6.0):
        # Already at default
        await query.answer("🔄 Filters already at default!", show_alert=True)
        return

    # Reset
    context.user_data['search_filters'] = {
        'genres': [],
        'year_from': None,
        'year_to': None,
        'min_rating': 6.0
    }

    await query.answer("🔄 Filters reset!", show_alert=True)
    await show_filter_menu(update, context, edit=True)

