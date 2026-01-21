# Telegram Bot Configuration

# ============================================
# BOT SETTINGS
# ============================================
BOT_TOKEN = "8569593826:AAH_0I5WS_y_D-fYYeCpKxwXCVQhhBCl9fo"

# PostgreSQL Database URL (Neon - Singapore)
DATABASE_URL = "postgresql://neondb_owner:npg_K6PCkLmdJpr2@ep-bitter-sunset-a1vhjzwx-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"

# Admin user IDs (can access /panel)
ADMIN_IDS = [7020461098]

# ============================================
# CHANNEL SETTINGS
# ============================================

# Source channel (private) - where you post videos
SOURCE_CHANNEL_ID = -1003573156420

# Target channels (public) - where bot posts
TARGET_CHANNELS = [
    {"id": -1003615561641, "name": "TARGET CHANNEL 1"},
    {"id": -1003344091364, "name": "TARGET Channel 2"},
]

# Required channels for verification
REQUIRED_CHANNELS = {
    "AFK_B": {
        "name": "AFK B",
        "link": "https://t.me/AFK_B",
        "type": "public"
    },
    -1003649746851: {
        "name": "test enti gravity",
        "link": "https://t.me/+T9OAFt-RbrY3ZmNl",
        "type": "private"
    },
}

# ============================================
# USER LIMITS
# ============================================
DAILY_DOWNLOAD_LIMIT = 300
PREMIUM_USERS = []  # User IDs with unlimited downloads

# ============================================
# MESSAGES
# ============================================
POST_TEMPLATE = """
🎬 {title}

📥 নিচে ক্লিক করে ভিডিও নিন!
"""

WELCOME_MESSAGE = """
🎉 **Welcome to our Bot!**

To use this bot, you need to join our channels first.

Please join all the channels below and click "✅ Joined" to verify.
"""

SUCCESS_MESSAGE = """
✅ **Congratulations!**

You have joined all required channels.
Now you can use all features of this bot.
"""

NOT_JOINED_MESSAGE = """
❌ **Verification Failed!**

You haven't joined all the required channels yet.
Please join all channels and try again.
"""

LIMIT_REACHED_MESSAGE = """
⏳ **Daily Limit Reached!**

আপনি আজকের জন্য সর্বোচ্চ {limit}টি video download করেছেন।
আগামীকাল আবার চেষ্টা করুন।
"""

VIDEO_NOT_FOUND_MESSAGE = """
❌ **Video Not Found!**

এই video টি পাওয়া যায়নি অথবা মুছে ফেলা হয়েছে।
"""

