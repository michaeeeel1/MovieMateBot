# bot/handlers/trending.py
"""
Trending Movies Handler

Shows trending movies from TMDb.
"""
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from bot.utils.tmdb_api import get_trending
from bot.keyboards.movie_keyboards import get_search_results_keyboard

logger = logging.getLogger(__name__)

# SHOW TRENDING OPTIONS

async def show_trending_options(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Show trending time window options

    Let user choose between daily and weekly trending.
    """
    keyboard = [
        [
            InlineKeyboardButton("🔥 Today", callback_data="trending_day"),
            InlineKeyboardButton("📅 This Week", callback_data="trending_week")
        ],
        [
            InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")
        ]
    ]

    await update.message.reply_text(
        "🔥 **Trending Movies**\n\n"
        "What's trending do you want to see?",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# SHOW TRENDING MOVIES

async def show_trending(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        time_window: str = 'week'
) -> None:
    """
    Show trending movies

    Args:
        update: Telegram update
        context: Callback context
        time_window: 'day' or 'week'
    """
    query = update.callback_query
    await query.answer()

    user = update.effective_user

    logger.info(f"User {user.id} requested trending movies ({time_window})")

    # Edit message to show loading
    await query.edit_message_text(
        f"🔥 Loading trending movies ({time_window})...",
        parse_mode='Markdown'
    )

    # Get trending movies
    movies = get_trending(media_type='movie', time_window=time_window)

    if not movies:
        await query.edit_message_text(
            "❌ **Oops!**\n\n"
            "Couldn't load trending movies right now.\n"
            "Please try again later! 🎬",
            parse_mode='Markdown'
        )
        return

    # Format header
    time_label = "Today" if time_window == 'day' else "This Week"
    header = (
        f"🔥 **Trending Movies - {time_label}**\n\n"
        f"Top {len(movies)} trending movies! 🚀\n"
        f"Tap to see details 👇"
    )

    # Get keyboard
    keyboard = get_search_results_keyboard(movies)

    # Store in context
    context.user_data['last_search_results'] = movies
    context.user_data['last_search_query'] = f'trending {time_window}'

    await query.edit_message_text(
        header,
        parse_mode='Markdown',
        reply_markup=keyboard
    )

    logger.info(f"Showed {len(movies)} trending movies to user {user.id}")

