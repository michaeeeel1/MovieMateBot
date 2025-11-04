# bot/handlers/start.py
"""
Start Command Handler
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from database.connection import get_session
from database import crud
from bot.keyboards.main_menu import get_main_menu_keyboard, get_welcome_keyboard

logger = logging.getLogger(__name__)

# START COMMAND

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /start command

    Registers new users or welcomes returning users.
    """
    user = update.effective_user

    logger.info(f"User {user.id} (@{user.username}) started the bot")

    with get_session() as session:
        # Try to get existing user
        db_user = crud.get_user_by_telegram_id(session, user.id)

        # Check if this is a new user
        is_new_user = (db_user is None)

        if is_new_user:
            # New user - create in database
            logger.info(f"Creating new user: {user.id}")

            db_user = crud.create_user(
                session=session,
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )

            # Check if creation was successful
            if not db_user:
                logger.error(f"❌ Failed to create user {user.id}")
                await update.message.reply_text(
                    "❌ Sorry, something went wrong. Please try again later."
                )
                return

            logger.info(f"✅ New user created successfully: {user.id}")

        else:
            # Existing user - just update last activity
            logger.info(f"Existing user, updating activity: {user.id}")
            crud.update_user_activity(session, db_user.id)

    # Send appropriate message based on whether user is new or returning
    if is_new_user:
        await send_welcome_message(update, user)
    else:
        await send_returning_message(update, user)


async def send_welcome_message(update: Update, user) -> None:
    """Send welcome message to new user"""
    welcome_text = (
        f"👋 Hello, {user.first_name}!\n\n"
        f"Welcome to **MovieMate** - your personal movie recommendation assistant! 🎬\n\n"
        f"I can help you:\n"
        f"🔍 Search for movies and TV series\n"
        f"🎯 Get personalized recommendations\n"
        f"⭐ Discover popular and trending content\n"
        f"❤️ Save your favorites\n"
        f"📊 Track your watch history\n\n"
        f"Ready to find your next favorite movie? 🍿"
    )

    await update.message.reply_text(
        welcome_text,
        parse_mode='Markdown',
        reply_markup=get_welcome_keyboard()
    )

    # Also send main menu
    menu_text = "👇 Use the menu below to navigate:"

    await update.message.reply_text(
        menu_text,
        reply_markup=get_main_menu_keyboard()
    )


async def send_returning_message(update: Update, user) -> None:
    """Send returning message to existing user"""
    with get_session() as session:
        db_user = crud.get_user_by_telegram_id(session, user.id)
        if db_user:
            stats = crud.get_user_stats(session, db_user.id)
        else:
            stats = {'favorites': 0, 'watched': 0, 'searches': 0}

    returning_text = (
        f"👋 Welcome back, {user.first_name}!\n\n"
        f"📊 **Your Stats:**\n"
        f"• Favorites: {stats.get('favorites', 0)} ❤️\n"
        f"• Watched: {stats.get('watched', 0)} 🎬\n"
        f"• Searches: {stats.get('searches', 0)} 🔍\n\n"
        f"What would you like to watch today? 🍿"
    )

    await update.message.reply_text(
        returning_text,
        parse_mode='Markdown',
        reply_markup=get_main_menu_keyboard()
    )

# HELP COMMAND

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command"""
    help_text = (
        "🤖 **MovieMate - Help**\n\n"
        "**Commands:**\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n\n"
        "**Features:**\n"
        "🔍 **Search Movies** - Find movies by title\n"
        "🔥 **Trending** - See what's trending now\n"
        "⭐ **Popular** - Most popular movies\n"
        "🎯 **Recommendations** - Personalized for you\n"
        "❤️ **My Favorites** - Your saved movies\n"
        "📊 **My Stats** - Your activity statistics\n\n"
        "**How it works:**\n"
        "1. Search for movies you like\n"
        "2. Add them to favorites\n"
        "3. Get personalized recommendations\n"
        "4. Discover new content!\n\n"
        "Powered by TMDb 🎬"
    )

    await update.message.reply_text(
        help_text,
        parse_mode='Markdown'
    )