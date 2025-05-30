# app/session_db.py

import os
import redis
from dotenv import load_dotenv

load_dotenv()
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

# Initialize Redis client or fallback to in-memory
try:
    _client = redis.from_url(redis_url)
    _client.ping()
    _USE_REDIS = True
except Exception:
    _USE_REDIS = False
    _cache = {}

def update_user_context(chat_id: int, context: str):
    key = f"context:{chat_id}"
    if _USE_REDIS:
        _client.set(key, context)
    else:
        _cache[chat_id] = context

def get_user_context(chat_id: int) -> str:
    key = f"context:{chat_id}"
    if _USE_REDIS:
        ctx = _client.get(key)
        return ctx.decode() if ctx else "general_conversation"
    else:
        return _cache.get(chat_id, "general_conversation")