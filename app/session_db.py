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

MAX_HISTORY_LEN = 5

def append_user_history(chat_id: int, message: str):
    key = f"history:{chat_id}"
    if _USE_REDIS:
        _client.rpush(key, message)
        _client.ltrim(key, -MAX_HISTORY_LEN, -1)  # Keep last N
    else:
        if chat_id not in _cache:
            _cache[chat_id] = []
        _cache[chat_id].append(message)
        _cache[chat_id] = _cache[chat_id][-MAX_HISTORY_LEN:]

def get_user_history(chat_id: int) -> list[str]:
    key = f"history:{chat_id}"
    if _USE_REDIS:
        return [m.decode() for m in _client.lrange(key, 0, -1)]
    else:
        return _cache.get(chat_id, [])