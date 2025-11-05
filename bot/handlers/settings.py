# bot/handlers/settings.py
"""
Settings Handler

User preferences and settings management.
"""

import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from database.connection import get_session
from database import crud

logger = logging.getLogger(__name__)

# SHOW SETTINGS MENU

async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Show settings menu

    Displays user's current settings and options to change them.
    """
    user = update.effective_user

    logger.info(f"User {user.id} opened settings")

    # Get current preferences - EXTRACT DATA INSIDE SESSION
    notifications = True
    min_rating = 6.0
    favorite_genres_count = 0

    with get_session() as session:
        db_user = crud.get_user_by_telegram_id(session, user.id)

        if not db_user:
            await update.message.reply_text(
                "❌ User not found. Please use /start to register."
            )
            return

        prefs = crud.get_user_preferences(session, db_user.id)

        if not prefs:
            # Create default preferences
            prefs = crud.create_default_preferences(session, db_user.id)

        # Extract data INSIDE session
        if prefs:
            notifications = prefs.notifications_enabled if prefs.notifications_enabled is not None else True
            min_rating = prefs.min_rating if prefs.min_rating else 6.0
            favorite_genres = prefs.favorite_genres if prefs.favorite_genres else []
            favorite_genres_count = len(favorite_genres)

    # Now we're outside session - use extracted data
    # Format settings text
    settings_text = (
        f"⚙️ **Settings**\n\n"
        f"**Current Settings:**\n"
        f"🔔 Notifications: {'✅ Enabled' if notifications else '❌ Disabled'}\n"
        f"⭐ Min Rating: {min_rating}/10\n"
        f"🎭 Favorite Genres: {favorite_genres_count} selected\n\n"
        f"Tap below to change settings:"
    )

    # Create keyboard
    keyboard = [
        [
            InlineKeyboardButton(
                f"🔔 Notifications: {'ON' if notifications else 'OFF'}",
                callback_data="settings_toggle_notif"
            )
        ],
        [
            InlineKeyboardButton(
                "⭐ Change Min Rating",
                callback_data="settings_min_rating"
            )
        ],
        [
            InlineKeyboardButton(
                "🎭 Select Favorite Genres",
                callback_data="settings_genres"
            )
        ],
        [
            InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")
        ]
    ]

    await update.message.reply_text(
        settings_text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# TOGGLE NOTIFICATIONS

async def toggle_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Toggle notifications on/off"""
    query = update.callback_query
    await query.answer()

    user = update.effective_user

    with get_session() as session:
        db_user = crud.get_user_by_telegram_id(session, user.id)
        if not db_user:
            return

        prefs = crud.get_user_preferences(session, db_user.id)
        if not prefs:
            return

        # Toggle
        new_value = not prefs.notifications_enabled
        crud.update_user_preferences(
            session,
            db_user.id,
            notifications_enabled=new_value
        )

        status = "enabled" if new_value else "disabled"
        await query.answer(f"🔔 Notifications {status}!", show_alert=True)

        # Update message
        await refresh_settings_message(query, db_user.id, session)

# SELECT MIN RATING

async def show_min_rating_options(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show minimum rating selection"""
    query = update.callback_query
    await query.answer()

    # Create rating keyboard
    keyboard = []

    for rating in [5.0, 6.0, 7.0, 7.5, 8.0, 8.5, 9.0]:
        keyboard.append([
            InlineKeyboardButton(
                f"⭐ {rating}/10",
                callback_data=f"set_rating_{rating}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton("🔙 Back to Settings", callback_data="back_to_settings")
    ])

    await query.edit_message_text(
        "⭐ **Select Minimum Rating**\n\n"
        "Movies below this rating won't appear in recommendations:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def set_min_rating(update: Update, context: ContextTypes.DEFAULT_TYPE, rating: float) -> None:
    """Set minimum rating preference"""
    query = update.callback_query
    await query.answer()

    user = update.effective_user

    with get_session() as session:
        db_user = crud.get_user_by_telegram_id(session, user.id)
        if not db_user:
            return

        crud.update_user_preferences(
            session,
            db_user.id,
            min_rating=rating
        )

        await query.answer(f"⭐ Min rating set to {rating}/10!", show_alert=True)

        # Back to settings
        await refresh_settings_message(query, db_user.id, session)

# HELPER: REFRESH SETTINGS MESSAGE

async def refresh_settings_message(query, user_id: int, session) -> None:
    """Refresh settings message with updated data"""

    # Extract data INSIDE session
    prefs = crud.get_user_preferences(session, user_id)

    if not prefs:
        return

    notifications = prefs.notifications_enabled if prefs.notifications_enabled is not None else True
    min_rating = prefs.min_rating if prefs.min_rating else 6.0
    favorite_genres = prefs.favorite_genres if prefs.favorite_genres else []
    favorite_genres_count = len(favorite_genres)

    # Now format message with extracted data
    settings_text = (
        f"⚙️ **Settings**\n\n"
        f"**Current Settings:**\n"
        f"🔔 Notifications: {'✅ Enabled' if notifications else '❌ Disabled'}\n"
        f"⭐ Min Rating: {min_rating}/10\n"
        f"🎭 Favorite Genres: {favorite_genres_count} selected\n\n"
        f"Tap below to change settings:"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                f"🔔 Notifications: {'ON' if notifications else 'OFF'}",
                callback_data="settings_toggle_notif"
            )
        ],
        [
            InlineKeyboardButton(
                "⭐ Change Min Rating",
                callback_data="settings_min_rating"
            )
        ],
        [
            InlineKeyboardButton(
                "🎭 Select Favorite Genres",
                callback_data="settings_genres"
            )
        ],
        [
            InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")
        ]
    ]

    await query.edit_message_text(
        settings_text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
