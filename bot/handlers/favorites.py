# bot/handlers/favorites.py
"""
Favorites Handler

Shows user's favorite movies.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from database.connection import get_session
from database import crud
from bot.keyboards.movie_keyboards import get_search_results_keyboard, get_back_to_menu_keyboard

logger = logging.getLogger(__name__)

# SHOW FAVORITES

async def show_favorites(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Show user's favorite movies

    Displays all movies user has marked as favorite.
    """
    user = update.effective_user

    logger.info(f"User {user.id} requested favorites")

    # Show loading
    loading_msg = await update.message.reply_text(
        "❤️ Loading your favorites...",
        parse_mode='Markdown'
    )

    # Get favorites from database - EXTRACT ALL DATA INSIDE SESSION
    movies = []

    with get_session() as session:
        db_user = crud.get_user_by_telegram_id(session, user.id)

        if not db_user:
            await loading_msg.delete()
            await update.message.reply_text(
                "❌ User not found. Please use /start to register."
            )
            return

        favorites = crud.get_user_favorites(session, db_user.id, limit=50)

        # Convert favorites to movie format INSIDE the session
        if favorites:
            for fav in favorites:
                # Extract year from release_date
                year = ''
                if fav.release_date and len(str(fav.release_date)) >= 4:
                    try:
                        year = int(str(fav.release_date)[:4])
                    except:
                        year = ''

                movies.append({
                    'tmdb_id': fav.tmdb_id,
                    'title': fav.title or 'Unknown',
                    'year': year,
                    'vote_average': fav.vote_average or 0,
                    'overview': fav.overview or '',
                    'genres': fav.genres or [],
                    'poster_path': fav.poster_path,
                    'poster_url': f"https://image.tmdb.org/t/p/w500{fav.poster_path}" if fav.poster_path else None
                })

    await loading_msg.delete()

    if not movies or len(movies) == 0:
        # No favorites yet
        await update.message.reply_text(
            "❤️ **My Favorites**\n\n"
            "You haven't added any favorites yet! 😢\n\n"
            "**How to add favorites:**\n"
            "1. Use 🔍 Search Movies\n"
            "2. Find a movie you like\n"
            "3. Tap ❤️ Add to Favorites\n\n"
            "Start exploring! 🎬",
            parse_mode='Markdown',
            reply_markup=get_back_to_menu_keyboard()
        )
        return

    # Format header
    header = (
        f"❤️ **My Favorites**\n\n"
        f"You have {len(movies)} favorite movie(s)! 🎬\n"
        f"Tap to see details 👇"
    )

    # Get keyboard
    keyboard = get_search_results_keyboard(movies)

    # Store in context
    context.user_data['last_search_results'] = movies
    context.user_data['last_search_query'] = 'my favorites'

    await update.message.reply_text(
        header,
        parse_mode='Markdown',
        reply_markup=keyboard
    )

    logger.info(f"Showed {len(movies)} favorites to user {user.id}")