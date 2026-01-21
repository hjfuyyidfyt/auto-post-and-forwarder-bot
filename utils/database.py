"""
Database utilities for PostgreSQL (Neon) storage
With connection pooling and auto-reconnect
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import pool
from contextlib import contextmanager
from datetime import datetime, date
from typing import Optional, Dict
import secrets
import string
import logging

from config import DATABASE_URL

logger = logging.getLogger(__name__)

# Connection pool
_pool = None


def get_pool():
    """Get connection pool."""
    global _pool
    if _pool is None:
        _pool = pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=DATABASE_URL
        )
        logger.info("Database connection pool created")
    return _pool


@contextmanager
def get_db():
    """Get database connection context manager."""
    conn = None
    try:
        conn = get_pool().getconn()
        conn.autocommit = True
        yield conn
    except Exception as e:
        logger.error(f"Database error: {e}")
        global _pool
        _pool = None  # Reset pool on error
        raise
    finally:
        if conn:
            try:
                get_pool().putconn(conn)
            except:
                pass


def init_database():
    """Initialize database tables."""
    with get_db() as conn:
        cur = conn.cursor()
        
        # Create videos table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                video_id VARCHAR(20) PRIMARY KEY,
                source_channel BIGINT NOT NULL,
                message_id BIGINT NOT NULL,
                title VARCHAR(255),
                thumbnail_id VARCHAR(255),
                downloads INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create users table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                joined_at DATE DEFAULT CURRENT_DATE,
                downloads_today INTEGER DEFAULT 0,
                last_download_date DATE,
                total_downloads INTEGER DEFAULT 0,
                is_premium BOOLEAN DEFAULT FALSE
            )
        """)
        
        # Create join_requests table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS join_requests (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                channel_id VARCHAR(100) NOT NULL,
                requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, channel_id)
            )
        """)
        
        # Create stats table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS stats (
                key VARCHAR(50) PRIMARY KEY,
                value INTEGER DEFAULT 0
            )
        """)
        
        cur.close()
        logger.info("Database tables initialized")


# ============================================
# VIDEO FUNCTIONS
# ============================================

def generate_video_id() -> str:
    """Generate unique video ID."""
    chars = string.ascii_lowercase + string.digits
    return "vid_" + ''.join(secrets.choice(chars) for _ in range(8))


def save_video(source_channel: int, message_id: int, title: str, thumbnail_id: str = None) -> str:
    """Save video to database and return unique ID."""
    with get_db() as conn:
        cur = conn.cursor()
        video_id = generate_video_id()
        
        cur.execute("""
            INSERT INTO videos (video_id, source_channel, message_id, title, thumbnail_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (video_id, source_channel, message_id, title, thumbnail_id))
        
        cur.close()
        update_stats("total_videos", 1)
        logger.info(f"Video saved: {video_id}")
        return video_id


def get_video(video_id: str) -> Optional[Dict]:
    """Get video by ID."""
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM videos WHERE video_id = %s", (video_id,))
        result = cur.fetchone()
        cur.close()
        return dict(result) if result else None


def delete_video(video_id: str) -> bool:
    """Delete video from database."""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM videos WHERE video_id = %s", (video_id,))
        deleted = cur.rowcount > 0
        cur.close()
        return deleted


def increment_downloads(video_id: str):
    """Increment download count for video."""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE videos SET downloads = downloads + 1 WHERE video_id = %s", (video_id,))
        cur.close()
        update_stats("total_downloads", 1)


def get_all_videos() -> Dict:
    """Get all videos."""
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM videos ORDER BY created_at DESC")
        results = cur.fetchall()
        cur.close()
        return {row['video_id']: dict(row) for row in results}


# ============================================
# USER FUNCTIONS
# ============================================

def get_user(user_id: int) -> Dict:
    """Get or create user data."""
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        result = cur.fetchone()
        
        if not result:
            cur.execute("INSERT INTO users (user_id) VALUES (%s) RETURNING *", (user_id,))
            result = cur.fetchone()
            update_stats("total_users", 1)
        
        cur.close()
        return dict(result)


def check_daily_limit(user_id: int, limit: int) -> tuple:
    """Check if user is within daily limit."""
    user = get_user(user_id)
    today = date.today()
    
    if user.get("last_download_date") != today:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE users SET downloads_today = 0, last_download_date = %s WHERE user_id = %s", (today, user_id))
            cur.close()
        user["downloads_today"] = 0
    
    remaining = limit - user["downloads_today"]
    return remaining > 0, remaining


def record_download(user_id: int):
    """Record a download for user."""
    with get_db() as conn:
        cur = conn.cursor()
        today = date.today()
        cur.execute("""
            UPDATE users SET downloads_today = downloads_today + 1, total_downloads = total_downloads + 1, last_download_date = %s
            WHERE user_id = %s
        """, (today, user_id))
        cur.close()


def get_all_users() -> Dict:
    """Get all users."""
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM users")
        results = cur.fetchall()
        cur.close()
        return {str(row['user_id']): dict(row) for row in results}


# ============================================
# JOIN REQUESTS
# ============================================

def add_join_request(user_id: int, channel_id):
    """Record a join request."""
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO join_requests (user_id, channel_id) VALUES (%s, %s)
                ON CONFLICT (user_id, channel_id) DO NOTHING
            """, (user_id, str(channel_id)))
            cur.close()
    except Exception as e:
        logger.error(f"Error adding join request: {e}")


def has_join_request(user_id: int, channel_id) -> bool:
    """Check if user has a join request."""
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM join_requests WHERE user_id = %s AND channel_id = %s", (user_id, str(channel_id)))
            result = cur.fetchone()
            cur.close()
            return result is not None
    except Exception as e:
        logger.error(f"Error checking join request: {e}")
        return False


def remove_join_request(user_id: int, channel_id):
    """Remove join request."""
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM join_requests WHERE user_id = %s AND channel_id = %s", (user_id, str(channel_id)))
            cur.close()
    except Exception as e:
        logger.error(f"Error removing join request: {e}")


# ============================================
# STATS
# ============================================

def update_stats(key: str, increment: int = 1):
    """Update a stat counter."""
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO stats (key, value) VALUES (%s, %s)
                ON CONFLICT (key) DO UPDATE SET value = stats.value + %s
            """, (key, increment, increment))
            cur.close()
    except Exception as e:
        logger.error(f"Error updating stats: {e}")


def get_stats() -> Dict:
    """Get all stats."""
    try:
        with get_db() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT * FROM stats")
            results = cur.fetchall()
            cur.close()
            return {row['key']: row['value'] for row in results}
    except:
        return {}


# Initialize on import
try:
    init_database()
except Exception as e:
    logger.error(f"Database init failed: {e}")
