"""
Start and verification handlers
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import TelegramError

from config import (
    REQUIRED_CHANNELS, WELCOME_MESSAGE, SUCCESS_MESSAGE, 
    NOT_JOINED_MESSAGE, DAILY_DOWNLOAD_LIMIT, PREMIUM_USERS,
    LIMIT_REACHED_MESSAGE, VIDEO_NOT_FOUND_MESSAGE
)
from utils.database import has_join_request, remove_join_request, check_daily_limit, record_download, get_user
from utils.keyboard import get_main_menu_keyboard, get_verification_keyboard
from utils.helpers import extract_video_id
from handlers.video import forward_video_to_user

logger = logging.getLogger(__name__)


async def check_membership(bot, user_id: int, channel_id) -> bool:
    """Check if user is member of channel."""
    try:
        if isinstance(channel_id, str) and not channel_id.startswith('-'):
            chat_id = f"@{channel_id}"
        else:
            chat_id = channel_id
        
        member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator', 'restricted']
    except TelegramError:
        return False


async def check_channel(bot, user_id: int, channel_id, channel_info: dict) -> bool:
    """Check if user satisfies channel requirement."""
    channel_type = channel_info.get("type", "public")
    
    if await check_membership(bot, user_id, channel_id):
        remove_join_request(user_id, channel_id)
        return True
    
    if channel_type == "private":
        return has_join_request(user_id, channel_id)
    
    return False


async def check_all_channels(bot, user_id: int) -> tuple[bool, list]:
    """Check all required channels."""
    not_joined = []
    
    for channel_id, channel_info in REQUIRED_CHANNELS.items():
        if not await check_channel(bot, user_id, channel_id, channel_info):
            not_joined.append(channel_id)
    
    return len(not_joined) == 0, not_joined


def create_channel_buttons(not_joined: list = None) -> InlineKeyboardMarkup:
    """Create channel join buttons."""
    keyboard = []
    
    for channel_id, channel_info in REQUIRED_CHANNELS.items():
        name = channel_info.get("name", str(channel_id))
        link = channel_info.get("link")
        typ = channel_info.get("type", "public")
        
        icon = "📩" if typ == "private" else "📢"
        status = "❌" if (not_joined and channel_id in not_joined) else "✅"
        
        keyboard.append([InlineKeyboardButton(f"{status} {icon} {name}", url=link)])
    
    keyboard.append([InlineKeyboardButton("✅ Joined", callback_data="verify")])
    
    return InlineKeyboardMarkup(keyboard)


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user_id = update.effective_user.id
    args = context.args
    
    # Check for deep link (video request)
    video_id = None
    if args and len(args) > 0:
        video_id = extract_video_id(args[0])
    
    # Check channel verification
    if REQUIRED_CHANNELS:
        all_ok, not_joined = await check_all_channels(context.bot, user_id)
        
        if not all_ok:
            # Store pending video request
            if video_id:
                context.user_data['pending_video'] = video_id
            
            await update.message.reply_text(
                WELCOME_MESSAGE,
                reply_markup=create_channel_buttons(not_joined),
                parse_mode='Markdown'
            )
            return
    
    # User is verified
    if video_id:
        await deliver_video(update, context, user_id, video_id)
    else:
        await update.message.reply_text(
            SUCCESS_MESSAGE,
            reply_markup=get_main_menu_keyboard(),
            parse_mode='Markdown'
        )


async def deliver_video(update, context, user_id: int, video_id: str):
    """Deliver video to user after verification."""
    
    # Check daily limit
    is_premium = user_id in PREMIUM_USERS
    
    if not is_premium:
        allowed, remaining = check_daily_limit(user_id, DAILY_DOWNLOAD_LIMIT)
        
        if not allowed:
            await update.message.reply_text(
                LIMIT_REACHED_MESSAGE.format(limit=DAILY_DOWNLOAD_LIMIT),
                parse_mode='Markdown'
            )
            return
    
    # Forward video
    success = await forward_video_to_user(context.bot, user_id, video_id)
    
    if success:
        record_download(user_id)
        
        # Show remaining downloads
        if not is_premium:
            _, remaining = check_daily_limit(user_id, DAILY_DOWNLOAD_LIMIT)
            await update.message.reply_text(
                f"✅ Video sent!\n\n📊 Today's remaining: {remaining}/{DAILY_DOWNLOAD_LIMIT}",
                reply_markup=get_main_menu_keyboard()
            )
        else:
            await update.message.reply_text(
                "✅ Video sent!",
                reply_markup=get_main_menu_keyboard()
            )
    else:
        await update.message.reply_text(
            VIDEO_NOT_FOUND_MESSAGE,
            reply_markup=get_main_menu_keyboard(),
            parse_mode='Markdown'
        )


async def handle_verify_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle verification button click."""
    query = update.callback_query
    user_id = query.from_user.id
    
    await query.answer()
    
    all_ok, not_joined = await check_all_channels(context.bot, user_id)
    
    if all_ok:
        # Check if there's a pending video
        pending_video = context.user_data.get('pending_video')
        
        if pending_video:
            del context.user_data['pending_video']
            await query.edit_message_text(SUCCESS_MESSAGE, parse_mode='Markdown')
            await deliver_video(update, context, user_id, pending_video)
        else:
            await query.edit_message_text(
                SUCCESS_MESSAGE,
                parse_mode='Markdown'
            )
            await query.message.reply_text(
                "Welcome! Use the menu below:",
                reply_markup=get_main_menu_keyboard()
            )
    else:
        await query.edit_message_text(
            NOT_JOINED_MESSAGE + "\n\n" + WELCOME_MESSAGE,
            reply_markup=create_channel_buttons(not_joined),
            parse_mode='Markdown'
        )


async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    help_text = """
📚 **Bot Help**

This bot helps you get videos from our channels.

**How to use:**
1. Join all required channels
2. Click on video buttons in public channels
3. Get the video directly here!

**Commands:**
/start - Start the bot
/help - Show this help

📢 = Public channel (must join)
📩 = Private channel (request to join)
    """
    await update.message.reply_text(
        help_text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode='Markdown'
    )
