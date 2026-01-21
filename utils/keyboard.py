"""
Reply keyboard utilities
"""

from telegram import ReplyKeyboardMarkup, KeyboardButton


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Get main menu keyboard for regular users."""
    keyboard = [
        [KeyboardButton("🔍 Search"), KeyboardButton("📊 My Stats")],
        [KeyboardButton("👤 Profile"), KeyboardButton("❓ Help")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_admin_keyboard() -> ReplyKeyboardMarkup:
    """Get admin panel keyboard."""
    keyboard = [
        [KeyboardButton("📤 Post Stats"), KeyboardButton("👥 Users")],
        [KeyboardButton("🎬 Videos"), KeyboardButton("⚙️ Settings")],
        [KeyboardButton("🔙 Back to Main")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_verification_keyboard() -> ReplyKeyboardMarkup:
    """Get keyboard shown during verification."""
    keyboard = [
        [KeyboardButton("✅ I've Joined")],
        [KeyboardButton("❓ Help")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
