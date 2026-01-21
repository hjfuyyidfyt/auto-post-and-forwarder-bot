"""
Common helper utilities
"""

import re
from telegram import Update
from config import ADMIN_IDS


def is_admin(user_id: int) -> bool:
    """Check if user is an admin."""
    return user_id in ADMIN_IDS


def get_user_id(update: Update) -> int:
    """Extract user ID from update."""
    if update.message:
        return update.message.from_user.id
    elif update.callback_query:
        return update.callback_query.from_user.id
    return 0


def extract_video_id(text: str) -> str:
    """Extract video ID from start parameter."""
    if text and text.startswith("vid_"):
        return text
    return None


def sanitize_title(caption: str) -> str:
    """Extract clean title from caption."""
    if not caption:
        return "Untitled Video"
    
    # Take first line or first 100 chars
    title = caption.split('\n')[0][:100]
    
    # Remove markdown formatting
    title = re.sub(r'[*_`\[\]]', '', title)
    
    return title.strip() or "Untitled Video"


def format_number(num: int) -> str:
    """Format number with K/M suffix."""
    if num >= 1_000_000:
        return f"{num/1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num/1_000:.1f}K"
    return str(num)
