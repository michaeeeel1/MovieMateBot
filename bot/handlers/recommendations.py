# bot/handlers/recommendations.py
"""
Recommendations Handler

Shows personalized movie recommendations.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from database.connection import get_session
from database import crud
from bot.utils.tmdb_api import discover_movies, get_movie_recommendations
from bot.keyboards.movie_keyboards import (
    get_search_results_keyboard,
    get_back_to_menu_keyboard
)

logger = logging.getLogger(__name__)

# SHOW RECOMMENDATIONS

async def show_recommendations(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Show personalized recommendations

    Based on user's favorite movies and genres.
    """
    user = update.effective_user

    logger.info(f"User {user.id} requested recommendations")

    # Show loading
    loading_msg = await update.message.reply_text(
        "🎯 Generating personalized recommendations...",
        parse_mode='Markdown'
    )

    # Get user's favorites - EXTRACT DATA INSIDE SESSION
    favorite_ids = []
    with get_session() as session:
        db_user = crud.get_user_by_telegram_id(session, user.id)

        if not db_user:
            await loading_msg.delete()
            await update.message.reply_text(
                "❌ User not found. Please use /start to register."
            )
            return

        favorites = crud.get_user_favorites(session, db_user.id, limit=10)

        # Extract TMDb IDs INSIDE the session
        if favorites:
            favorite_ids = [fav.tmdb_id for fav in favorites]

    # Check if user has favorites
    if not favorite_ids or len(favorite_ids) == 0:
        await loading_msg.delete()
        await update.message.reply_text(
            "🎯 **Personalized Recommendations**\n\n"
            "I need to learn your taste first! 😊\n\n"
            "**To get recommendations:**\n"
            "1. Use 🔍 Search Movies\n"
            "2. Add movies you like to ❤️ Favorites\n"
            "3. Come back here for recommendations!\n\n"
            "The more favorites you add, the better recommendations you'll get! 🎬",
            parse_mode='Markdown',
            reply_markup=get_back_to_menu_keyboard()
        )
        return

    # Get recommendations based on first favorite
    first_favorite_id = favorite_ids[0]
    movies = get_movie_recommendations(first_favorite_id, page=1)

    # If no recommendations from first favorite, try discover with good ratings
    if not movies or len(movies) == 0:
        logger.info("No recommendations from favorites, using discover")
        movies = discover_movies(min_rating=7.0, sort_by='popularity.desc', page=1)

    await loading_msg.delete()

    if not movies or len(movies) == 0:
        await update.message.reply_text(
            "❌ **Oops!**\n\n"
            "Couldn't generate recommendations right now.\n"
            "Please try again later! 🎬",
            parse_mode='Markdown',
            reply_markup=get_back_to_menu_keyboard()
        )
        return

    # Format header
    header = (
        f"🎯 **Personalized Recommendations**\n\n"
        f"Based on your favorites! ❤️\n"
        f"You might like these {len(movies)} movies 🎬\n"
        f"Tap to see details 👇"
    )

    # Get keyboard
    keyboard = get_search_results_keyboard(movies)

    # Store in context
    context.user_data['last_search_results'] = movies
    context.user_data['last_search_query'] = 'recommendations'

    await update.message.reply_text(
        header,
        parse_mode='Markdown',
        reply_markup=keyboard
    )

    logger.info(f"Showed {len(movies)} recommendations to user {user.id}")


async def show_similar(update: Update, context: ContextTypes.DEFAULT_TYPE, tmdb_id: int) -> None:
    """
    Show similar movies to a specific movie

    Args:
        update: Telegram update
        context: Callback context
        tmdb_id: TMDb movie ID
    """
    query = update.callback_query
    await query.answer()

    user = update.effective_user

    logger.info(f"User {user.id} requested similar movies for {tmdb_id}")

    # Edit message to show loading
    try:
        await query.edit_message_text(
            "🎯 Finding similar movies...",
            parse_mode='Markdown'
        )
    except:
        # If can't edit (photo message), send new
        await query.message.reply_text(
            "🎯 Finding similar movies...",
            parse_mode='Markdown'
        )
        return

    # Get similar movies
    movies = get_movie_recommendations(tmdb_id, page=1)

    if not movies or len(movies) == 0:
        await query.edit_message_text(
            "❌ **Oops!**\n\n"
            "Couldn't find similar movies right now.\n"
            "Please try again later! 🎬",
            parse_mode='Markdown',
            reply_markup=get_back_to_menu_keyboard()
        )
        return

    # Format header
    header = (
        f"🎯 **Similar Movies**\n\n"
        f"Movies similar to your selection! 🎬\n"
        f"Found {len(movies)} recommendations 👇"
    )

    # Get keyboard
    keyboard = get_search_results_keyboard(movies)

    # Store in context
    context.user_data['last_search_results'] = movies
    context.user_data['last_search_query'] = 'similar movies'

    await query.edit_message_text(
        header,
        parse_mode='Markdown',
        reply_markup=keyboard
    )

    logger.info(f"Showed {len(movies)} similar movies to user {user.id}")