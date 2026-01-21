# Telegram Channel Verification Bot

A Python Telegram bot that requires users to join specific channels before using the bot.

## Features

- ✅ Welcome message on `/start`
- ✅ Checks if user has joined all required channels
- ✅ Shows channel buttons with join links
- ✅ "Joined" verification button
- ✅ Allows bot usage only after joining all channels

## Setup Instructions

### 1. Create a Bot

1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow the instructions
3. Copy the bot token you receive

### 2. Add Bot as Admin to Channels

**Important:** The bot must be an administrator in all required channels to check user membership.

1. Go to each channel → Settings → Administrators
2. Add your bot as an administrator
3. The bot only needs "Read Messages" permission

### 3. Configure the Bot

Edit `config.py`:

```python
# Add your bot token
BOT_TOKEN = "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"

# Add your channel usernames (without @)
REQUIRED_CHANNELS = [
    "yourchannel1",
    "yourchannel2",
]
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the Bot

```bash
python bot.py
```

## How It Works

1. User sends `/start` to the bot
2. Bot checks if user is a member of all required channels
3. If **joined all channels**: Shows success message, user can use the bot
4. If **not joined**: Shows channel buttons with:
   - ✅ Channels already joined
   - ❌ Channels not yet joined
   - "✅ Joined" verification button at the bottom
5. User joins channels and clicks "Joined" button
6. Bot re-verifies membership and updates the message

## File Structure

```
├── bot.py           # Main bot code
├── config.py        # Configuration (token, channels, messages)
├── requirements.txt # Python dependencies
└── README.md        # This file
```

## Customization

Edit `config.py` to customize:

- `WELCOME_MESSAGE` - Message shown when user needs to join channels
- `SUCCESS_MESSAGE` - Message shown after successful verification
- `NOT_JOINED_MESSAGE` - Message shown when verification fails

## Requirements

- Python 3.8+
- python-telegram-bot 20.0+

## Troubleshooting

### "Error checking membership"
- Make sure the bot is an admin in all required channels
- Verify the channel username/ID is correct

### Bot not responding
- Check if the bot token is correct
- Make sure the bot is running (`python bot.py`)

## License

MIT License
