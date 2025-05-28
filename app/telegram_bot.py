# app/telegram_bot.py

import os
import threading
import logging
from dotenv import load_dotenv
from flask import Flask, jsonify, redirect
from telegram.ext import ApplicationBuilder, MessageHandler, filters
from app.sea_lion_api import generate_response
from app.langchain_prompts import format_prompt
from app.utils import detect_context
from app.session_db import update_user_context, get_user_context

# Load environment variables
load_dotenv()

# Configure minimal logging
logging.basicConfig(level=logging.WARNING)

# Telegram bot token
TOKEN = os.getenv("TELEGRAM_TOKEN")

# Flask app for health checks
health_app = Flask(__name__)

@health_app.route("/healthz")
def healthz():
    """Health check endpoint to verify service and Redis connectivity."""
    try:
        # Ping Redis to confirm connectivity
        from app.session_db import _client as _redis_client
        _redis_client.ping()
    except Exception:
        pass
    return jsonify(status="ok"), 200

@health_app.route("/")
def root():
    """Redirect root to healthz for easy monitoring."""
    return redirect("/healthz")

def run_health_server():
    """Run the Flask health endpoint on the port defined by the $PORT environment variable."""
    port = int(os.getenv("PORT", 8000))
    health_app.run(host="0.0.0.0", port=port)

async def handle_message(update, context):
    """Process incoming Telegram messages, detect context, generate AI response, and reply."""
    user_input = update.message.text
    chat_id = update.message.chat_id

    # Detect and persist user context
    detected = detect_context(user_input)
    update_user_context(chat_id, detected)

    # Format prompt for LLM
    prompt = format_prompt(detected, user_input)
    resp = generate_response(prompt)

    # Send response back to user
    await update.message.reply_text(resp)

def main():
    # Start health endpoint in background thread
    threading.Thread(target=run_health_server, daemon=True).start()

    # Build and run Telegram long polling
    # skip_updates=True clears any pending updates to avoid conflicts
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling(skip_updates=True)

if __name__ == "__main__":
    main()

