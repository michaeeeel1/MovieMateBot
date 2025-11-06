# bot/handlers/tv_shows.py
"""
TV Shows Handler

Handles TV show search and display.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from bot.utils.tmdb_api import (
    search_tv_shows,
    get_tv_show_details,
    get_tv_trailer_url
)
from bot.keyboards.movie_keyboards import (
    get_search_results_keyboard,
    get_movie_details_keyboard,
    get_back_to_menu_keyboard
)
from bot.utils.formatters import (
    format_search_results_header,
    format_no_results
)
from database.connection import get_session
from database import crud

logger = logging.getLogger(__name__)

# Conversation states
WAITING_FOR_TV_SEARCH = 1


# ============================================
# START TV SEARCH
# ============================================

async def start_tv_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start TV show search conversation"""
    await update.message.reply_text(
        "📺 **Search TV Shows**\n\n"
        "Enter the TV show title you're looking for:\n\n"
        "Examples:\n"
        "• Breaking Bad\n"
        "• Game of Thrones\n"
        "• Stranger Things\n\n"
        "Or send /cancel to go back.",
        parse_mode='Markdown'
    )

    return WAITING_FOR_TV_SEARCH


# ============================================
# HANDLE TV SEARCH QUERY
# ============================================

async def handle_tv_search_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle TV show search query"""
    query = update.message.text.strip()
    user = update.effective_user

    if not query:
        await update.message.reply_text(
            "❌ Please enter a valid TV show title!"
        )
        return WAITING_FOR_TV_SEARCH

    logger.info(f"User {user.id} searching TV shows: {query}")

    # Show searching message
    searching_msg = await update.message.reply_text(
        f"🔍 Searching for TV shows: _{query}_...",
        parse_mode='Markdown'
    )

    # Search TV shows
    results = search_tv_shows(query)

    # Save to history
    with get_session() as session:
        db_user = crud.get_user_by_telegram_id(session, user.id)
        if db_user:
            crud.add_search_history(
                session=session,
                user_id=db_user.id,
                query=query,
                search_type='tv',
                results_count=len(results)
            )

    await searching_msg.delete()

    if not results:
        await update.message.reply_text(
            format_no_results(query).replace("movies", "TV shows"),
            parse_mode='Markdown',
            reply_markup=get_back_to_menu_keyboard()
        )
        return ConversationHandler.END

    # Show results
    header = format_search_results_header(query, len(results)).replace("movie(s)", "TV show(s)")
    keyboard = get_search_results_keyboard(results)

    # Store in context
    context.user_data['last_search_results'] = results
    context.user_data['last_search_query'] = query
    context.user_data['last_search_type'] = 'tv'

    await update.message.reply_text(
        header,
        parse_mode='Markdown',
        reply_markup=keyboard
    )

    logger.info(f"Found {len(results)} TV shows for: {query}")

    return ConversationHandler.END


# ============================================
# SHOW TV SHOW DETAILS
# ============================================

async def show_tv_details(update: Update, context: ContextTypes.DEFAULT_TYPE, tv_id: int) -> None:
    """Show detailed TV show information"""
    query = update.callback_query
    await query.answer()

    user = update.effective_user

    await query.edit_message_text(
        f"⏳ Loading TV show details...",
        parse_mode='Markdown'
    )

    # Get TV show details
    show = get_tv_show_details(tv_id)

    if not show:
        await query.edit_message_text(
            "❌ Sorry, couldn't load TV show details.\n\n"
            "Please try again later.",
            reply_markup=get_back_to_menu_keyboard()
        )
        return

    # Check if in favorites
    is_favorite = False
    is_watched = False
    with get_session() as session:
        db_user = crud.get_user_by_telegram_id(session, user.id)
        if db_user:
            is_favorite = crud.is_in_favorites(session, db_user.id, tv_id)
            is_watched = crud.is_watched(session, db_user.id, tv_id)

    # Format TV show card
    text = format_tv_card(show)

    # Get keyboard
    keyboard = get_movie_details_keyboard(tv_id, is_favorite, is_watched)

    # Try to send with poster
    poster_url = show.get('poster_url')

    if poster_url:
        try:
            await query.message.reply_photo(
                photo=poster_url,
                caption=text,
                parse_mode='Markdown',
                reply_markup=keyboard
            )
            await query.delete_message()
        except Exception as e:
            logger.warning(f"Failed to send poster: {e}")
            await query.edit_message_text(
                text,
                parse_mode='Markdown',
                reply_markup=keyboard
            )
    else:
        await query.edit_message_text(
            text,
            parse_mode='Markdown',
            reply_markup=keyboard
        )

    logger.info(f"Showed TV show {tv_id} to user {user.id}")


def format_tv_card(show: dict) -> str:
    """Format TV show data for display"""
    title = show.get('title', 'Unknown')
    year = show.get('year', '')
    rating = show.get('vote_average', 0)
    votes = show.get('vote_count', 0)
    overview = show.get('overview', 'No description available.')
    genres = show.get('genres', [])

    # TV-specific info
    seasons = show.get('number_of_seasons', 0)
    episodes = show.get('number_of_episodes', 0)
    status = show.get('status', 'Unknown')
    networks = show.get('networks', [])

    # Truncate overview
    if len(overview) > 300:
        overview = overview[:297] + '...'

    # Build message
    text = f"📺 **{title}**"

    if year:
        text += f" ({year})"

    text += "\n\n"

    # Rating
    if rating > 0:
        stars = "⭐" * int(rating / 2)
        text += f"{stars} **{rating}/10** ({votes:,} votes)\n"

    # Genres
    if genres:
        genres_text = ", ".join(genres[:3])
        text += f"🎭 {genres_text}\n"

    # TV info
    if seasons > 0:
        text += f"📺 {seasons} Season{'s' if seasons != 1 else ''}, {episodes} Episodes\n"

    if status:
        status_emoji = "🟢" if status in ["Returning Series", "In Production"] else "🔴"
        text += f"{status_emoji} Status: {status}\n"

    if networks:
        text += f"📡 {', '.join(networks[:2])}\n"

    text += f"\n{overview}"

    return text


# ============================================
# CANCEL TV SEARCH
# ============================================

async def cancel_tv_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel TV show search"""
    await update.message.reply_text(
        "📺 TV show search cancelled.\n\n"
        "Use the menu buttons to navigate! 👇"
    )

    return ConversationHandler.END