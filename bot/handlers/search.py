# bot/handlers/search.py
"""
Search Handler

Handles movie search functionality.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from bot.utils.tmdb_api import search_movies, get_movie_details, get_movie_trailer_url
from bot.utils.formatters import (
    format_movie_card,
    format_search_results_header,
    format_no_results
)
from bot.keyboards.movie_keyboards import (
    get_search_results_keyboard,
    get_movie_details_keyboard,
    get_back_to_menu_keyboard
)
from database.connection import get_session
from database import crud

logger = logging.getLogger(__name__)

# Conversation states
WAITING_FOR_SEARCH = 1

# START SEARCH

async def start_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Start search conversation

    Returns:
        Conversation state
    """
    await update.message.reply_text(
        "🔍 **Search Movies**\n\n"
        "Enter the movie title you're looking for:\n\n"
        "Examples:\n"
        "• Inception\n"
        "• The Matrix\n"
        "• Interstellar\n\n"
        "Or send /cancel to go back.",
        parse_mode='Markdown'
    )

    return WAITING_FOR_SEARCH

# HANDLE SEARCH QUERY

async def handle_search_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle search query from user

    Returns:
        ConversationHandler.END
    """
    query = update.message.text.strip()
    user = update.effective_user

    if not query:
        await update.message.reply_text(
            "❌ Please enter a valid movie title!"
        )
        return WAITING_FOR_SEARCH

    logger.info(f"User {user.id} searching for: {query}")

    # Show "searching..." message
    searching_msg = await update.message.reply_text(
        f"🔍 Searching for: _{query}_...",
        parse_mode='Markdown'
    )

    # Search movies
    results = search_movies(query)

    # Save search to history
    with get_session() as session:
        db_user = crud.get_user_by_telegram_id(session, user.id)
        if db_user:
            crud.add_search_history(
                session=session,
                user_id=db_user.id,
                query=query,
                search_type='text',
                results_count=len(results)
            )

    # Delete "searching..." message
    await searching_msg.delete()

    if not results:
        # No results
        await update.message.reply_text(
            format_no_results(query),
            parse_mode='Markdown',
            reply_markup=get_back_to_menu_keyboard()
        )
        return ConversationHandler.END

    # Show results
    header = format_search_results_header(query, len(results))
    keyboard = get_search_results_keyboard(results)

    # Store results in context for later use
    context.user_data['last_search_results'] = results
    context.user_data['last_search_query'] = query

    await update.message.reply_text(
        header,
        parse_mode='Markdown',
        reply_markup=keyboard
    )

    logger.info(f"Found {len(results)} results for: {query}")

    return ConversationHandler.END

# SHOW MOVIE DETAILS


async def show_movie_details(update: Update, context: ContextTypes.DEFAULT_TYPE, tmdb_id: int) -> None:
    """
    Show detailed information about a movie

    Args:
        update: Telegram update
        context: Callback context
        tmdb_id: TMDb movie ID
    """
    query = update.callback_query
    await query.answer()

    user = update.effective_user

    # Edit message to show loading
    await query.edit_message_text(
        f"⏳ Loading movie details...",
        parse_mode='Markdown'
    )

    # Get movie details
    movie = get_movie_details(tmdb_id)

    if not movie:
        await query.edit_message_text(
            "❌ Sorry, couldn't load movie details.\n\n"
            "Please try again later.",
            reply_markup=get_back_to_menu_keyboard()
        )
        return

    # Check if in favorites and watched
    is_favorite = False
    is_watched = False
    with get_session() as session:
        db_user = crud.get_user_by_telegram_id(session, user.id)
        if db_user:
            is_favorite = crud.is_in_favorites(session, db_user.id, tmdb_id)
            is_watched = crud.is_watched(session, db_user.id, tmdb_id)

    # Format movie card
    text = format_movie_card(movie)

    # Add additional details
    runtime = movie.get('runtime', 0)
    if runtime > 0:
        hours = runtime // 60
        minutes = runtime % 60
        text += f"\n\n⏱️ Duration: {hours}h {minutes}min"

    tagline = movie.get('tagline', '')
    if tagline:
        text += f"\n💬 _{tagline}_"

    # Get keyboard
    keyboard = get_movie_details_keyboard(tmdb_id, is_favorite, is_watched)

    # Try to send with poster
    poster_url = movie.get('poster_url')

    if poster_url:
        try:
            # Send photo with caption
            await query.message.reply_photo(
                photo=poster_url,
                caption=text,
                parse_mode='Markdown',
                reply_markup=keyboard
            )
            # Delete loading message
            await query.delete_message()

        except Exception as e:
            logger.warning(f"Failed to send poster: {e}")
            # Fallback: send as text
            await query.edit_message_text(
                text,
                parse_mode='Markdown',
                reply_markup=keyboard
            )
    else:
        # No poster - send as text
        await query.edit_message_text(
            text,
            parse_mode='Markdown',
            reply_markup=keyboard
        )

    logger.info(f"Showed details for movie {tmdb_id} to user {user.id}")

# CANCEL SEARCH

async def cancel_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel search conversation"""
    await update.message.reply_text(
        "🔍 Search cancelled.\n\n"
        "Use the menu buttons to navigate! 👇"
    )

    return ConversationHandler.END