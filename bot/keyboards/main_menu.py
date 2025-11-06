# bot/keyboards/main_menu.py
"""
Main Menu Keyboards
"""

from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton

# MAIN MENU

def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Get main menu keyboard"""
    keyboard = [
        [
            KeyboardButton("🎬 Movies"),
            KeyboardButton("📺 TV Shows")
        ],
        [
            KeyboardButton("🔥 Trending"),
            KeyboardButton("⭐ Popular")
        ],
        [
            KeyboardButton("🎯 Recommendations"),
            KeyboardButton("❤️ My Favorites")
        ],
        [
            KeyboardButton("📊 My Stats"),
            KeyboardButton("⚙️ Settings")
        ],
        [
            KeyboardButton("❓ Help")
        ]
    ]

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )

# WELCOME KEYBOARD

def get_welcome_keyboard() -> InlineKeyboardMarkup:
    """Get welcome keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("🚀 Get Started", callback_data="get_started")
        ],
        [
            InlineKeyboardButton("ℹ️ About", callback_data="about")
        ]
    ]

    return InlineKeyboardMarkup(keyboard)