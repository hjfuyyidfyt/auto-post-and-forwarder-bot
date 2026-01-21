"""
Content Distribution Telegram Bot
- Monitors source channel for videos
- Posts to public channels
- Delivers videos to verified users
"""

import asyncio
import logging
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, ChatJoinRequestHandler, filters
)

from config import BOT_TOKEN, SOURCE_CHANNEL_ID, ADMIN_IDS
from handlers.start import handle_start, handle_verify_callback, handle_help
from handlers.admin import handle_panel, handle_admin_button
from handlers.user import handle_user_button
from handlers.video import handle_channel_post
from utils.database import add_join_request

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# ============================================
# JOIN REQUEST HANDLER
# ============================================

async def on_join_request(update: Update, context):
    """Handle channel join requests."""
    req = update.chat_join_request
    user_id = req.from_user.id
    chat_id = req.chat.id
    
    logger.info(f"Join request: {req.from_user.first_name} ({user_id}) -> {chat_id}")
    add_join_request(user_id, chat_id)


# ============================================
# MESSAGE ROUTER
# ============================================

async def route_message(update: Update, context):
    """Route text messages to appropriate handler."""
    if not update.message or not update.message.text:
        return
    
    text = update.message.text
    user_id = update.effective_user.id
    
    # Admin buttons
    admin_buttons = ["📤 Post Stats", "👥 Users", "🎬 Videos", "⚙️ Settings", "🔙 Back to Main"]
    if text in admin_buttons and user_id in ADMIN_IDS:
        await handle_admin_button(update, context)
        return
    
    # User buttons
    user_buttons = ["🔍 Search", "📊 My Stats", "👤 Profile", "❓ Help", "✅ I've Joined"]
    if text in user_buttons:
        await handle_user_button(update, context)
        return


# ============================================
# MAIN
# ============================================

async def main():
    """Start the bot."""
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("[ERROR] Set BOT_TOKEN in config.py")
        return
    
    print("=" * 50)
    print("CONTENT DISTRIBUTION BOT")
    print("=" * 50)
    print(f"Source Channel: {SOURCE_CHANNEL_ID or 'Not configured'}")
    print(f"Admins: {ADMIN_IDS or 'None'}")
    print("=" * 50)
    
    # Build application
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .read_timeout(10)
        .write_timeout(10)
        .connect_timeout(10)
        .build()
    )
    
    # Command handlers
    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(CommandHandler("help", handle_help))
    app.add_handler(CommandHandler("panel", handle_panel))
    
    # Callback handlers
    app.add_handler(CallbackQueryHandler(handle_verify_callback, pattern="^verify$"))
    
    # Admin delete callback
    from handlers.admin import handle_video_delete_callback
    app.add_handler(CallbackQueryHandler(handle_video_delete_callback, pattern="^del_|^admin_back$"))
    
    # Message handlers
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        route_message
    ))
    
    # Channel post handler (for video AND photo detection)
    app.add_handler(MessageHandler(
        filters.ChatType.CHANNEL & (filters.VIDEO | filters.PHOTO),
        handle_channel_post
    ))
    
    # Join request handler
    app.add_handler(ChatJoinRequestHandler(on_join_request))
    
    print("\nBot starting...")
    print("Press Ctrl+C to stop\n")
    
    # Initialize and run
    await app.initialize()
    await app.start()
    await app.updater.start_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )
    
    # Keep running until interrupted
    try:
        while True:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()


if __name__ == '__main__':
    asyncio.run(main())
