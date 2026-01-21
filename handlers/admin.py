"""
Admin panel handlers
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import ADMIN_IDS
from utils.database import get_stats, get_all_videos, get_all_users, delete_video
from utils.keyboard import get_admin_keyboard, get_main_menu_keyboard
from utils.helpers import is_admin, format_number

logger = logging.getLogger(__name__)


async def handle_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /panel command."""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ You don't have access to admin panel.")
        return
    
    await update.message.reply_text(
        "⚙️ **Admin Panel**\n\nSelect an option:",
        reply_markup=get_admin_keyboard(),
        parse_mode='Markdown'
    )


async def handle_admin_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin panel buttons."""
    user_id = update.effective_user.id
    text = update.message.text
    
    if not is_admin(user_id):
        return
    
    if text == "📤 Post Stats":
        await show_post_stats(update)
    
    elif text == "👥 Users":
        await show_user_stats(update)
    
    elif text == "🎬 Videos":
        await show_video_list(update, context)
    
    elif text == "⚙️ Settings":
        await show_settings(update)
    
    elif text == "🔙 Back to Main":
        await update.message.reply_text(
            "Main menu:",
            reply_markup=get_main_menu_keyboard()
        )
    
    # Delete video handling
    elif text.startswith("🗑️ Delete: "):
        video_id = text.replace("🗑️ Delete: ", "").strip()
        await delete_video_handler(update, context, video_id)


async def show_post_stats(update: Update):
    """Show post/video statistics."""
    stats = get_stats()
    
    text = f"""
📊 **Post Statistics**

🎬 Total Videos: {format_number(stats.get('total_videos', 0))}
📥 Total Downloads: {format_number(stats.get('total_downloads', 0))}
👥 Total Users: {format_number(stats.get('total_users', 0))}
    """
    
    await update.message.reply_text(
        text,
        reply_markup=get_admin_keyboard(),
        parse_mode='Markdown'
    )


async def show_user_stats(update: Update):
    """Show user statistics."""
    users = get_all_users()
    stats = get_stats()
    
    # Count active today
    from datetime import date
    today = date.today().isoformat()
    active_today = sum(1 for u in users.values() if u.get('last_download_date') == today)
    
    text = f"""
👥 **User Statistics**

📊 Total Users: {format_number(len(users))}
🟢 Active Today: {format_number(active_today)}
    """
    
    await update.message.reply_text(
        text,
        reply_markup=get_admin_keyboard(),
        parse_mode='Markdown'
    )


async def show_video_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show recent videos with delete options."""
    videos = get_all_videos()
    
    if not videos:
        await update.message.reply_text(
            "No videos yet.",
            reply_markup=get_admin_keyboard()
        )
        return
    
    # Show last 10 videos with inline delete buttons
    text = "🎬 **Recent Videos:**\n\n"
    
    sorted_videos = sorted(
        videos.items(), 
        key=lambda x: x[1].get('created_at', ''), 
        reverse=True
    )[:10]
    
    keyboard = []
    
    for vid_id, vid_data in sorted_videos:
        title = vid_data.get('title', 'Untitled')[:25]
        downloads = vid_data.get('downloads', 0)
        text += f"• `{vid_id}` - {title}... ({downloads}📥)\n"
        
        # Add delete button for each video
        keyboard.append([
            InlineKeyboardButton(f"🗑️ {vid_id}", callback_data=f"del_{vid_id}")
        ])
    
    text += f"\n_Total: {len(videos)} videos_\n\nClick to delete:"
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="admin_back")])
    
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


async def handle_video_delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle video delete callback."""
    query = update.callback_query
    user_id = query.from_user.id
    
    if not is_admin(user_id):
        await query.answer("❌ Not authorized")
        return
    
    await query.answer()
    data = query.data
    
    if data == "admin_back":
        await query.edit_message_text(
            "⚙️ **Admin Panel**\n\nSelect an option:",
            parse_mode='Markdown'
        )
        return
    
    if data.startswith("del_"):
        video_id = data.replace("del_", "")
        success = delete_video(video_id)
        
        if success:
            await query.edit_message_text(
                f"✅ Video `{video_id}` deleted successfully!",
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(
                f"❌ Video `{video_id}` not found!",
                parse_mode='Markdown'
            )
    
    elif data.startswith("confirm_del_"):
        video_id = data.replace("confirm_del_", "")
        success = delete_video(video_id)
        
        if success:
            await query.edit_message_text(
                f"✅ Video `{video_id}` deleted!",
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(
                f"❌ Failed to delete video.",
                parse_mode='Markdown'
            )


async def delete_video_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, video_id: str):
    """Handle video deletion from text command."""
    success = delete_video(video_id)
    
    if success:
        await update.message.reply_text(
            f"✅ Video `{video_id}` deleted!",
            reply_markup=get_admin_keyboard(),
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            f"❌ Video not found!",
            reply_markup=get_admin_keyboard()
        )


async def show_settings(update: Update):
    """Show settings info."""
    from config import DAILY_DOWNLOAD_LIMIT, SOURCE_CHANNEL_ID, TARGET_CHANNELS
    
    text = f"""
⚙️ **Settings**

📥 Daily Limit: {DAILY_DOWNLOAD_LIMIT}
📺 Source Channel: `{SOURCE_CHANNEL_ID or 'Not set'}`
📢 Target Channels: {len(TARGET_CHANNELS)}

_Edit config.py to change settings_
    """
    
    await update.message.reply_text(
        text,
        reply_markup=get_admin_keyboard(),
        parse_mode='Markdown'
    )
