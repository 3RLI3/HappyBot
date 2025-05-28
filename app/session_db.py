# app/session_db.py

import os
import redis
from dotenv import load_dotenv

load_dotenv()
# Connect to Render Key Value via private internal URL
redis_url = os.getenv("REDIS_URL")
_client = redis.from_url(redis_url)  # redis-py auto-detects scheme :contentReference[oaicite:4]{index=4}

def update_user_context(chat_id: int, context: str):
    """
    Store the latest context for a user.
    Uses SET command.
    """
    _client.set(f"context:{chat_id}", context)  # Simple SET operation :contentReference[oaicite:5]{index=5}

def get_user_context(chat_id: int) -> str:
    """
    Retrieve the last context for a user.
    Returns 'general_conversation' if none found.
    """
    ctx = _client.get(f"context:{chat_id}")  # GET operation :contentReference[oaicite:6]{index=6}
    return ctx.decode() if ctx else "general_conversation"
