# bot/main.py
"""
Telegram Bot Initialization
"""

import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

from database.connection import get_session
from config import settings
from database import crud
from bot.handlers import (start, search, popular,
                        trending, favorites, recommendations,
                        settings as settings_handler, advanced_search
                          )

logger = logging.getLogger(__name__)

# ERROR HANDLER

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors"""
    logger.error(f"Exception while handling update: {context.error}")

    if update:
        logger.error(f"Update that caused error: {update}")

# CALLBACK QUERY HANDLER

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle callback queries from inline keyboards"""
    query = update.callback_query
    await query.answer()

    callback_data = query.data

    logger.info(f"Callback: {callback_data} from user {query.from_user.id}")

    # Get Started
    if callback_data == "get_started":
        await query.edit_message_text(
            "🎬 Great! Let's get started!\n\n"
            "Use the menu buttons below to:\n"
            "🔍 Search for movies\n"
            "🔥 See trending content\n"
            "⭐ Discover popular movies\n\n"
            "Try searching for your favorite movie! 🍿"
        )

    # About
    elif callback_data == "about":
        about_text = (
            "ℹ️ **About MovieMate**\n\n"
            "🎬 Your personal movie recommendation assistant!\n\n"
            "**Features:**\n"
            "• Search movies and TV series\n"
            "• Get personalized recommendations\n"
            "• Save favorites\n"
            "• Track watch history\n"
            "• Discover trending content\n\n"
            "**Data Source:** TMDb (themoviedb.org)\n"
            "**Version:** 1.0 Beta\n"
            "**Developer:** @megaknight24\n\n"
            "Made with ❤️ and Python 🐍"
        )
        await query.edit_message_text(
            about_text,
            parse_mode='Markdown'
        )

    # Movie Details
    elif callback_data.startswith("movie_"):
        tmdb_id = int(callback_data.replace("movie_", ""))
        await search.show_movie_details(update, context, tmdb_id)

    # Add to Favorites
    elif callback_data.startswith("fav_"):
        tmdb_id = int(callback_data.replace("fav_", ""))
        await handle_add_favorite(update, context, tmdb_id)

    # Remove from Favorites
    elif callback_data.startswith("unfav_"):
        tmdb_id = int(callback_data.replace("unfav_", ""))
        await handle_remove_favorite(update, context, tmdb_id)

    # Mark as Watched
    elif callback_data.startswith("watched_"):
        tmdb_id = int(callback_data.replace("watched_", ""))
        await handle_mark_watched(update, context, tmdb_id)

    # Remove from Watched (NEW!)
    elif callback_data.startswith("unwatched_"):
        tmdb_id = int(callback_data.replace("unwatched_", ""))
        await handle_unwatched(update, context, tmdb_id)

    # Similar Movies
    elif callback_data.startswith("similar_"):
        tmdb_id = int(callback_data.replace("similar_", ""))
        await recommendations.show_similar(update, context, tmdb_id)

    # Watch Trailer
    elif callback_data.startswith("trailer_"):
        tmdb_id = int(callback_data.replace("trailer_", ""))
        await handle_trailer(update, context, tmdb_id)

    # Trending Options
    elif callback_data == "trending_day":
        await trending.show_trending(update, context, 'day')

    elif callback_data == "trending_week":
        await trending.show_trending(update, context, 'week')

    # Main Menu
    elif callback_data == "main_menu":
        from bot.keyboards.main_menu import get_main_menu_keyboard

        try:
            # Try to edit message
            await query.edit_message_text(
                "🏠 **Main Menu**\n\n"
                "Use the buttons below to navigate! 👇",
                parse_mode='Markdown'
            )
        except:
            # If can't edit (e.g., message with photo), send new message
            await query.message.reply_text(
                "🏠 **Main Menu**\n\n"
                "Use the buttons below to navigate! 👇",
                parse_mode='Markdown',
                reply_markup=get_main_menu_keyboard()
            )

    # Back to Search
    elif callback_data == "back_search":
        if 'last_search_results' in context.user_data:
            from bot.utils.formatters import format_search_results_header
            from bot.keyboards.movie_keyboards import get_search_results_keyboard

            results = context.user_data['last_search_results']
            query_text = context.user_data.get('last_search_query', 'your search')

            header = format_search_results_header(query_text, len(results))
            keyboard = get_search_results_keyboard(results)

            try:
                await query.edit_message_text(
                    header,
                    parse_mode='Markdown',
                    reply_markup=keyboard
                )
            except:
                await query.message.reply_text(
                    header,
                    parse_mode='Markdown',
                    reply_markup=keyboard
                )
        else:
            await query.edit_message_text(
                "🔍 No recent search.\n\n"
                "Use 🔍 Search Movies to find movies!",
                parse_mode='Markdown'
            )

    elif callback_data == "settings_toggle_notif":
        await settings_handler.toggle_notifications(update, context)

    elif callback_data == "settings_min_rating":
        await settings_handler.show_min_rating_options(update, context)

    elif callback_data == "settings_genres":  # ← ДОБАВЛЯЕМ!
        await query.answer("🎭 Genre selection coming soon!", show_alert=True)

    elif callback_data.startswith("set_rating_"):
        rating = float(callback_data.replace("set_rating_", ""))
        await settings_handler.set_min_rating(update, context, rating)

    elif callback_data == "back_to_settings":
        query = update.callback_query
        user = query.from_user

        with get_session() as session:
            db_user = crud.get_user_by_telegram_id(session, user.id)
            if db_user:
                await settings_handler.refresh_settings_message(query, db_user.id, session)

    # Advanced Search callbacks
    elif callback_data == "adv_search_genre":
        await advanced_search.show_genre_selection(update, context)

    elif callback_data == "adv_search_year":
        await advanced_search.show_year_selection(update, context)

    elif callback_data == "adv_search_rating":
        await advanced_search.show_rating_selection(update, context)

    elif callback_data == "adv_search_execute":
        await advanced_search.execute_search(update, context)

    elif callback_data == "adv_search_reset":
        await advanced_search.reset_filters(update, context)

    elif callback_data.startswith("toggle_genre_"):
        genre_name = callback_data.replace("toggle_genre_", "")
        await advanced_search.toggle_genre(update, context, genre_name)

    elif callback_data == "genre_done":
        await advanced_search.show_filter_menu(update, context, edit=True)

    elif callback_data == "genre_clear":
        context.user_data['search_filters']['genres'] = []
        await advanced_search.show_genre_selection(update, context)

    elif callback_data.startswith("year_range_"):
        parts = callback_data.replace("year_range_", "").split("_")
        year_from = int(parts[0])
        year_to = int(parts[1])
        await advanced_search.set_year_range(update, context, year_from, year_to)

    elif callback_data == "year_done":
        await advanced_search.show_filter_menu(update, context, edit=True)

    elif callback_data.startswith("adv_rating_"):
        rating = float(callback_data.replace("adv_rating_", ""))
        await advanced_search.set_rating(update, context, rating)

    elif callback_data == "rating_done":
        await advanced_search.show_filter_menu(update, context, edit=True)

    # Unknown callback
    else:
        logger.warning(f"Unknown callback: {callback_data}")
        await query.answer("⚠️ Unknown action", show_alert=True)

# MESSAGE HANDLER

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text messages from reply keyboard"""
    text = update.message.text

    logger.info(f"Message: '{text}' from user {update.effective_user.id}")

    if text == "🔍 Search Movies":
        await search.start_search(update, context)

    elif text == "🔍 Advanced Search":  # ← НОВАЯ КНОПКА
        await advanced_search.start_advanced_search(update, context)

    elif text == "🔥 Trending":
        await trending.show_trending_options(update, context)

    elif text == "⭐ Popular":
        await popular.show_popular(update, context)

    elif text == "🎯 Recommendations":
        await recommendations.show_recommendations(update, context)

    elif text == "❤️ My Favorites":
        await favorites.show_favorites(update, context)

    elif text == "📊 My Stats":
        from database.connection import get_session
        from database import crud

        with get_session() as session:
            db_user = crud.get_user_by_telegram_id(session, update.effective_user.id)
            if db_user:
                stats = crud.get_user_stats(session, db_user.id)

                stats_text = (
                    "📊 **Your Statistics**\n\n"
                    f"❤️ Favorites: {stats.get('favorites', 0)}\n"
                    f"🎬 Watched: {stats.get('watched', 0)}\n"
                    f"🔍 Searches: {stats.get('searches', 0)}\n\n"
                    "Keep using the bot to build your stats! 💪"
                )

                await update.message.reply_text(
                    stats_text,
                    parse_mode='Markdown'
                )


    elif text == "⚙️ Settings":
        await settings_handler.show_settings(update, context)

    elif text == "❓ Help":
        await start.help_command(update, context)

    else:
        await update.message.reply_text(
            f"🤔 I don't understand '{text}' yet.\n\n"
            f"Please use the menu buttons below! 👇"
        )

# MARK AS WATCHED HANDLER

async def handle_mark_watched(update: Update, context: ContextTypes.DEFAULT_TYPE, tmdb_id: int) -> None:
    """Mark movie as watched or remove from watched"""
    query = update.callback_query

    user = update.effective_user

    # Check if already watched
    is_already_watched = False
    with get_session() as session:
        db_user = crud.get_user_by_telegram_id(session, user.id)
        if db_user:
            is_already_watched = crud.is_watched(session, db_user.id, tmdb_id)

    if is_already_watched:
        # Already watched - offer to remove
        await query.answer("⚠️ Already marked as watched!", show_alert=True)
        return

    # Not watched yet - mark as watched
    await query.answer("✅ Marking as watched...")

    # Get movie details
    from bot.utils.tmdb_api import get_movie_details
    movie = get_movie_details(tmdb_id)

    if not movie:
        await query.answer("❌ Error loading movie", show_alert=True)
        return

    # Add to watch history in database
    with get_session() as session:
        db_user = crud.get_user_by_telegram_id(session, user.id)
        if db_user:
            result = crud.add_to_watch_history(
                session=session,
                user_id=db_user.id,
                tmdb_id=tmdb_id,
                media_type='movie',
                title=movie['title'],
                poster_path=movie.get('poster_path'),
                release_date=movie.get('release_date'),
                genres=movie.get('genres', [])
            )

            if result:
                await query.answer("✅ Marked as watched! 🎬", show_alert=True)
                logger.info(f"User {user.id} marked movie {tmdb_id} as watched")

                # Update keyboard to show "Remove from Watched" button
                from bot.keyboards.movie_keyboards import get_movie_details_keyboard

                # Check if in favorites
                is_favorite = crud.is_in_favorites(session, db_user.id, tmdb_id)
                keyboard = get_movie_details_keyboard(tmdb_id, is_favorite=is_favorite, is_watched=True)

                try:
                    await query.edit_message_reply_markup(reply_markup=keyboard)
                except:
                    pass
            else:
                await query.answer("⚠️ Already in watch history!", show_alert=True)


async def handle_unwatched(update: Update, context: ContextTypes.DEFAULT_TYPE, tmdb_id: int) -> None:
    """Remove movie from watched"""
    query = update.callback_query
    await query.answer("🗑️ Removing from watched...")

    user = update.effective_user

    # Remove from database
    with get_session() as session:
        db_user = crud.get_user_by_telegram_id(session, user.id)
        if db_user:
            result = crud.remove_from_watch_history(session, db_user.id, tmdb_id)

            if result:
                await query.answer("🗑️ Removed from watched", show_alert=True)

                # Update keyboard
                from bot.keyboards.movie_keyboards import get_movie_details_keyboard

                # Check if in favorites
                is_favorite = crud.is_in_favorites(session, db_user.id, tmdb_id)
                keyboard = get_movie_details_keyboard(tmdb_id, is_favorite=is_favorite, is_watched=False)

                try:
                    await query.edit_message_reply_markup(reply_markup=keyboard)
                except:
                    pass
            else:
                await query.answer("❌ Error removing", show_alert=True)

# TRAILER HANDLER

async def handle_trailer(update: Update, context: ContextTypes.DEFAULT_TYPE, tmdb_id: int) -> None:
    """Show trailer link"""
    query = update.callback_query

    from bot.utils.tmdb_api import get_movie_trailer_url

    trailer_url = get_movie_trailer_url(tmdb_id)

    if trailer_url:
        await query.answer()
        await query.message.reply_text(
            f"🎥 **Watch Trailer**\n\n"
            f"[Click here to watch on YouTube]({trailer_url})",
            parse_mode='Markdown'
        )
    else:
        await query.answer("❌ Trailer not available", show_alert=True)

# FAVORITES HANDLERS

async def handle_add_favorite(update: Update, context: ContextTypes.DEFAULT_TYPE, tmdb_id: int) -> None:
    """Add movie to favorites"""
    query = update.callback_query
    await query.answer("❤️ Adding to favorites...")

    user = update.effective_user

    # Get movie details
    from bot.utils.tmdb_api import get_movie_details
    movie = get_movie_details(tmdb_id)

    if not movie:
        await query.answer("❌ Error loading movie", show_alert=True)
        return

    # Add to database
    with get_session() as session:
        db_user = crud.get_user_by_telegram_id(session, user.id)
        if db_user:
            result = crud.add_to_favorites(
                session=session,
                user_id=db_user.id,
                tmdb_id=tmdb_id,
                media_type='movie',
                title=movie['title'],
                poster_path=movie.get('poster_path'),
                backdrop_path=movie.get('backdrop_path'),
                overview=movie.get('overview'),
                release_date=movie.get('release_date'),
                vote_average=movie.get('vote_average'),
                genres=movie.get('genres', [])
            )

            if result:
                await query.answer("❤️ Added to favorites!", show_alert=True)

                # Update keyboard
                from bot.keyboards.movie_keyboards import get_movie_details_keyboard
                keyboard = get_movie_details_keyboard(tmdb_id, is_favorite=True)

                try:
                    await query.edit_message_reply_markup(reply_markup=keyboard)
                except:
                    pass
            else:
                await query.answer("⚠️ Already in favorites!", show_alert=True)


async def handle_remove_favorite(update: Update, context: ContextTypes.DEFAULT_TYPE, tmdb_id: int) -> None:
    """Remove movie from favorites"""
    query = update.callback_query
    await query.answer("💔 Removing from favorites...")

    user = update.effective_user

    # Remove from database
    with get_session() as session:
        db_user = crud.get_user_by_telegram_id(session, user.id)
        if db_user:
            result = crud.remove_from_favorites(session, db_user.id, tmdb_id)

            if result:
                await query.answer("💔 Removed from favorites", show_alert=True)

                # Update keyboard
                from bot.keyboards.movie_keyboards import get_movie_details_keyboard
                keyboard = get_movie_details_keyboard(tmdb_id, is_favorite=False)

                try:
                    await query.edit_message_reply_markup(reply_markup=keyboard)
                except:
                    pass
            else:
                await query.answer("❌ Error removing", show_alert=True)

# APPLICATION SETUP

def setup_handlers(application: Application) -> None:
    """Register all handlers"""
    logger.info("Registering handlers...")

    # Command handlers
    application.add_handler(CommandHandler("start", start.start_command))
    application.add_handler(CommandHandler("help", start.help_command))

    # Search conversation handler
    search_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(
                filters.Regex("^🔍 Search Movies$"),
                search.start_search
            )
        ],
        states={
            search.WAITING_FOR_SEARCH: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    search.handle_search_query
                )
            ]
        },
        fallbacks=[
            CommandHandler("cancel", search.cancel_search)
        ]
    )

    application.add_handler(search_conv_handler)

    # Callback query handler
    application.add_handler(CallbackQueryHandler(handle_callback_query))

    # Message handler
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message)
    )

    # Error handler
    application.add_error_handler(error_handler)

    logger.info("✅ Handlers registered")

# MAIN FUNCTION

def main() -> None:
    """Start the bot"""
    logger.info("Initializing bot...")

    # Create application
    application = (
        Application.builder()
        .token(settings.BOT_TOKEN)
        .build()
    )

    logger.info("✅ Application created")

    # Register handlers
    setup_handlers(application)

    # Run bot
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )

    logger.info("Bot stopped")


if __name__ == "__main__":
    main()

