# app/telegram_bot.py

import os
import threading
import logging
from dotenv import load_dotenv
from flask import Flask, jsonify
from telegram.ext import ApplicationBuilder, MessageHandler, filters
from sea_lion_api import generate_response
from langchain_prompts import format_prompt
from utils import detect_context
from session_db import update_user_context, get_user_context

# Load environment variables
load_dotenv()

# Configure minimal logging
logging.basicConfig(level=logging.WARNING)

# Telegram token
TOKEN = os.getenv("TELEGRAM_TOKEN")

# Flask app for health checks
health_app = Flask(__name__)

@health_app.route("/healthz")
def healthz():
    """Health check endpoint to verify service and Redis connectivity."""
    try:
        from session_db import _client as _redis_client
        if _redis_client.ping():
            return jsonify(status="ok"), 200
    except Exception:
        pass
    return jsonify(status="error"), 500

def run_health_server():
    """Run the Flask health endpoint on port 8000."""
    health_app.run(host="0.0.0.0", port=8000)

async def handle_message(update, context):
    user_input = update.message.text
    chat_id = update.message.chat_id

    # Retrieve and update context in Redis
    last_context = get_user_context(chat_id)
    detected_context = detect_context(user_input)
    update_user_context(chat_id, detected_context)

    # Format prompt and generate AI response
    prompt = format_prompt(detected_context, user_input)
    response = generate_response(prompt)
    await update.message.reply_text(response)

def main():
    # Start health endpoint in background
    threading.Thread(target=run_health_server, daemon=True).start()

    # Start Telegram long-polling in single process
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()


