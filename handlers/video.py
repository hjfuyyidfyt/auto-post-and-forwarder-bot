"""
Video handler - detects videos in source channel and posts to target channels

Supports 2 methods:
1. Media Group: Photo + Video posted together → Immediately posts
2. Reply Method: Video/Photo posted first, then reply with Photo/Video → Posts when pair complete

Single video/photo without pair will be STORED but NOT posted until paired via reply.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import TelegramError

from config import SOURCE_CHANNEL_ID, TARGET_CHANNELS
from utils.database import save_video, get_video, increment_downloads
from utils.helpers import sanitize_title

logger = logging.getLogger(__name__)

# Store media group data temporarily
media_groups = {}

# Store unpaired posts (waiting for reply to complete pair)
# {message_id: {type, file_id, caption, chat_id, message_id}}
pending_posts = {}


async def handle_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle new posts in source channel."""
    message = update.channel_post
    
    if not message:
        return
    
    # Check if from source channel
    if SOURCE_CHANNEL_ID and message.chat.id != SOURCE_CHANNEL_ID:
        return
    
    # Method 1: Media Group (Photo + Video together) - Post immediately
    if message.media_group_id:
        await handle_media_group(update, context)
        return
    
    # Method 2: Reply - Check if this is a reply to complete a pair
    if message.reply_to_message:
        await handle_reply_method(update, context)
        return
    
    # Single post without reply - STORE but do NOT post
    if message.video:
        pending_posts[message.message_id] = {
            "type": "video",
            "file_id": message.video.file_id,
            "message_id": message.message_id,
            "chat_id": message.chat.id,
            "caption": message.caption
        }
        logger.info(f"Video STORED (waiting for reply): msg_id={message.message_id}")
    
    elif message.photo:
        pending_posts[message.message_id] = {
            "type": "photo",
            "file_id": message.photo[-1].file_id,
            "message_id": message.message_id,
            "chat_id": message.chat.id,
            "caption": message.caption
        }
        logger.info(f"Photo STORED (waiting for reply): msg_id={message.message_id}")


async def handle_media_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Method 1: Handle media group (Photo + Video together) - Posts immediately."""
    message = update.channel_post
    group_id = message.media_group_id
    
    if group_id not in media_groups:
        media_groups[group_id] = {
            "photo": None,
            "video_file_id": None,
            "video_message_id": None,
            "caption": None,
            "chat_id": message.chat.id
        }
    
    group = media_groups[group_id]
    
    if message.photo:
        group["photo"] = message.photo[-1].file_id
        if message.caption:
            group["caption"] = message.caption
        logger.info(f"Media group {group_id}: Photo received")
    
    if message.video:
        group["video_file_id"] = message.video.file_id
        group["video_message_id"] = message.message_id
        if message.caption:
            group["caption"] = message.caption
        logger.info(f"Media group {group_id}: Video received")
    
    # Process when both available
    if group["photo"] and group["video_file_id"]:
        logger.info(f"Media group {group_id}: COMPLETE - posting...")
        
        title = sanitize_title(group["caption"])
        
        video_id = save_video(
            source_channel=group["chat_id"],
            message_id=group["video_message_id"],
            title=title,
            thumbnail_id=group["photo"]
        )
        
        await post_to_channels(context.bot, video_id, title, thumbnail_photo_id=group["photo"])
        del media_groups[group_id]


async def handle_reply_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Method 2: Handle Reply to complete pairs.
    
    Supports:
    - Photo reply to Video → Photo = Thumbnail
    - Video reply to Photo → Photo = Thumbnail
    - Video reply to Video → Second Video's thumbnail = Thumbnail, First Video = Content
    """
    message = update.channel_post
    replied_to = message.reply_to_message
    replied_msg_id = replied_to.message_id
    
    logger.info(f"Reply detected to message {replied_msg_id}")
    
    thumbnail_id = None
    content_video_message_id = None
    caption = None
    
    # Get the replied-to message data (either from pending_posts or direct)
    replied_data = pending_posts.get(replied_msg_id)
    
    # Case 1: Current message is a VIDEO replying to something
    if message.video:
        caption = message.caption or (replied_to.caption if replied_to else None)
        
        # Check what was replied to
        if replied_to.photo:
            # Video reply to Photo → Photo = Thumbnail, This Video = Content
            thumbnail_id = replied_to.photo[-1].file_id
            content_video_message_id = message.message_id
            
        elif replied_data and replied_data["type"] == "photo":
            # Video reply to stored Photo
            thumbnail_id = replied_data["file_id"]
            content_video_message_id = message.message_id
            if not caption:
                caption = replied_data.get("caption")
                
        elif replied_to.video:
            # Video reply to Video → Second Video's thumbnail = Thumbnail, First Video = Content
            # Get thumbnail from second video (current message)
            if message.video.thumbnail:
                thumbnail_id = message.video.thumbnail.file_id
            content_video_message_id = replied_to.message_id  # First video is content
            
        elif replied_data and replied_data["type"] == "video":
            # Video reply to stored Video
            if message.video.thumbnail:
                thumbnail_id = message.video.thumbnail.file_id
            content_video_message_id = replied_data["message_id"]  # First video is content
            if not caption:
                caption = replied_data.get("caption")
    
    # Case 2: Current message is a PHOTO replying to something
    elif message.photo:
        thumbnail_id = message.photo[-1].file_id
        caption = message.caption or (replied_to.caption if replied_to else None)
        
        # Check if replied message is a video
        if replied_to.video:
            content_video_message_id = replied_to.message_id
        elif replied_data and replied_data["type"] == "video":
            content_video_message_id = replied_data["message_id"]
            if not caption:
                caption = replied_data.get("caption")
    
    # If we have both thumbnail and video - POST!
    if thumbnail_id and content_video_message_id:
        logger.info("Reply method: Pair COMPLETE - posting...")
        
        title = sanitize_title(caption)
        
        video_id = save_video(
            source_channel=message.chat.id,
            message_id=content_video_message_id,
            title=title,
            thumbnail_id=thumbnail_id
        )
        
        await post_to_channels(context.bot, video_id, title, thumbnail_photo_id=thumbnail_id)
        
        # Clean up pending
        if replied_msg_id in pending_posts:
            del pending_posts[replied_msg_id]
            logger.info(f"Cleaned up pending post {replied_msg_id}")
    else:
        logger.info("Reply method: Incomplete pair - need thumbnail and video")


async def post_to_channels(bot, video_id: str, title: str, thumbnail_photo_id: str):
    """Post video preview with photo thumbnail to all target channels."""
    
    if not TARGET_CHANNELS:
        logger.warning("No target channels configured")
        return
    
    bot_username = (await bot.get_me()).username
    button_url = f"https://t.me/{bot_username}?start={video_id}"
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📥 Get Video", url=button_url)]
    ])
    
    post_caption = f"🎬 <b>{title}</b>\n\n📥 নিচে ক্লিক করে ভিডিও নিন!"
    
    for channel in TARGET_CHANNELS:
        channel_id = channel.get("id")
        channel_name = channel.get("name", "Unknown")
        
        try:
            await bot.send_photo(
                chat_id=channel_id,
                photo=thumbnail_photo_id,
                caption=post_caption,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            logger.info(f"Posted to {channel_name} ✓")
        except TelegramError as e:
            logger.error(f"Failed to post to {channel_name}: {e}")


async def forward_video_to_user(bot, user_id: int, video_id: str) -> bool:
    """Forward video from source channel to user."""
    video_data = get_video(video_id)
    
    if not video_data:
        return False
    
    try:
        await bot.forward_message(
            chat_id=user_id,
            from_chat_id=video_data["source_channel"],
            message_id=video_data["message_id"]
        )
        increment_downloads(video_id)
        return True
    except TelegramError as e:
        logger.error(f"Failed to forward video: {e}")
        return False
