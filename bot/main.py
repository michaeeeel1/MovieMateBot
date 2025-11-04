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
    ContextTypes
)

from config import settings
from bot.handlers import start

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

    if callback_data == "get_started":
        await query.edit_message_text(
            "🎬 Great! Let's get started!\n\n"
            "Use the menu buttons below to:\n"
            "🔍 Search for movies\n"
            "🔥 See trending content\n"
            "⭐ Discover popular movies\n\n"
            "Try searching for your favorite movie! 🍿"
        )

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
            "**Developer:** @michaeeeel1\n\n"
            "Made with ❤️ and Python 🐍"
        )
        await query.edit_message_text(
            about_text,
            parse_mode='Markdown'
        )

# MESSAGE HANDLER

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text messages from reply keyboard"""
    text = update.message.text

    logger.info(f"Message: '{text}' from user {update.effective_user.id}")

    if text == "🔍 Search Movies":
        await update.message.reply_text(
            "🔍 **Search Movies**\n\n"
            "This feature is coming soon! 🚧\n\n"
            "You'll be able to search for any movie by title.\n"
            "Stay tuned! 🎬"
        )

    elif text == "🔥 Trending":
        await update.message.reply_text(
            "🔥 **Trending Movies**\n\n"
            "This feature is coming soon! 🚧\n\n"
            "You'll see what's trending right now.\n"
            "Stay tuned! 🎬"
        )

    elif text == "⭐ Popular":
        await update.message.reply_text(
            "⭐ **Popular Movies**\n\n"
            "This feature is coming soon! 🚧\n\n"
            "You'll see the most popular movies.\n"
            "Stay tuned! 🎬"
        )

    elif text == "🎯 Recommendations":
        await update.message.reply_text(
            "🎯 **Personalized Recommendations**\n\n"
            "This feature is coming soon! 🚧\n\n"
            "You'll get recommendations based on your favorites.\n"
            "Stay tuned! 🎬"
        )

    elif text == "❤️ My Favorites":
        await update.message.reply_text(
            "❤️ **My Favorites**\n\n"
            "This feature is coming soon! 🚧\n\n"
            "You'll see all your favorite movies here.\n"
            "Stay tuned! 🎬"
        )

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
        await update.message.reply_text(
            "⚙️ **Settings**\n\n"
            "Settings are coming soon! 🚧\n\n"
            "You'll be able to customize your preferences.\n"
            "Stay tuned! 🎬"
        )

    elif text == "❓ Help":
        await start.help_command(update, context)

    else:
        await update.message.reply_text(
            f"🤔 I don't understand '{text}' yet.\n\n"
            f"Please use the menu buttons below! 👇"
        )

# APPLICATION SETUP

def setup_handlers(application: Application) -> None:
    """Register all handlers"""
    logger.info("Registering handlers...")

    # Command handlers
    application.add_handler(CommandHandler("start", start.start_command))
    application.add_handler(CommandHandler("help", start.help_command))

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

