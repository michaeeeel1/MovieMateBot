# bot/handlers/popular.py
"""
Popular Movies Handler

Shows popular movies from TMDb.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from bot.utils.tmdb_api import get_popular_movies
from bot.utils.formatters import format_search_results_header
from bot.keyboards.movie_keyboards import get_search_results_keyboard

logger = logging.getLogger(__name__)

# SHOW POPULAR MOVIES

async def show_popular(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Show popular movies

    Displays top popular movies from TMDb.
    """
    user = update.effective_user

    logger.info(f"User {user.id} requested popular movies")

    # Show loading message
    loading_msg = await update.message.reply_text(
        "⭐ Loading popular movies...",
        parse_mode='Markdown'
    )

    # Get popular movies
    movies = get_popular_movies(page=1)

    # Delete loading message
    await loading_msg.delete()

    if not movies:
        await update.message.reply_text(
            "❌ **Oops!**\n\n"
            "Couldn't load popular movies right now.\n"
            "Please try again later! 🎬",
            parse_mode='Markdown'
        )
        return

    # Format header
    header = (
        "⭐ **Popular Movies Right Now**\n\n"
        f"Top {len(movies)} most popular movies! 🔥\n"
        f"Tap to see details 👇"
    )

    # Get keyboard
    keyboard = get_search_results_keyboard(movies)

    # Store in context for navigation
    context.user_data['last_search_results'] = movies
    context.user_data['last_search_query'] = 'popular movies'

    await update.message.reply_text(
        header,
        parse_mode='Markdown',
        reply_markup=keyboard
    )

    logger.info(f"Showed {len(movies)} popular movies to user {user.id}")