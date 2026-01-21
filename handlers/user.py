"""
User profile and stats handlers
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from config import DAILY_DOWNLOAD_LIMIT, PREMIUM_USERS
from utils.database import get_user, check_daily_limit
from utils.keyboard import get_main_menu_keyboard
from utils.helpers import format_number

logger = logging.getLogger(__name__)


async def handle_user_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user menu buttons."""
    text = update.message.text
    user_id = update.effective_user.id
    
    if text == "🔍 Search":
        await handle_search(update, context)
    
    elif text == "📊 My Stats":
        await handle_my_stats(update, context)
    
    elif text == "👤 Profile":
        await handle_profile(update, context)
    
    elif text == "❓ Help":
        from handlers.start import handle_help
        await handle_help(update, context)
    
    elif text == "✅ I've Joined":
        # Re-trigger verification
        from handlers.start import handle_start
        await handle_start(update, context)


async def handle_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle search button."""
    await update.message.reply_text(
        "🔍 **Search**\n\nSearch feature coming soon!\n\n"
        "For now, find videos in our public channels.",
        reply_markup=get_main_menu_keyboard(),
        parse_mode='Markdown'
    )


async def handle_my_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle my stats button."""
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    is_premium = user_id in PREMIUM_USERS
    _, remaining = check_daily_limit(user_id, DAILY_DOWNLOAD_LIMIT)
    
    status = "⭐ Premium" if is_premium else "👤 Regular"
    limit_text = "Unlimited" if is_premium else f"{remaining}/{DAILY_DOWNLOAD_LIMIT}"
    
    text = f"""
📊 **Your Statistics**

🏷️ Status: {status}
📥 Today's Remaining: {limit_text}
📦 Total Downloads: {format_number(user.get('total_downloads', 0))}
📅 Joined: {user.get('joined_at', 'Unknown')}
    """
    
    await update.message.reply_text(
        text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode='Markdown'
    )


async def handle_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle profile button."""
    user = update.effective_user
    user_data = get_user(user.id)
    
    is_premium = user.id in PREMIUM_USERS
    status = "⭐ Premium Member" if is_premium else "👤 Regular Member"
    
    text = f"""
👤 **Your Profile**

🆔 ID: `{user.id}`
👤 Name: {user.first_name}
🏷️ Status: {status}
📅 Member Since: {user_data.get('joined_at', 'Unknown')}
    """
    
    await update.message.reply_text(
        text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode='Markdown'
    )
