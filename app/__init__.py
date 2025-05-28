# === app/__init__.py ===
"""
App package initializer for the Companion Bot.
"""

from .telegram_bot import main
__all__ = ["main"]
from .session_db import init_db
# Initialize the database when the app is imported
init_db()
