import os
import threading
import logging
import tempfile
from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, send_from_directory, request
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    PollHandler,
    ContextTypes,
    filters,
)

import speech_recognition as sr
from gtts import gTTS
from pydub import AudioSegment

from app.sea_lion_api import generate_response
from app.langchain_prompts import format_prompt
from app.utils import detect_context
from app.session_db import update_user_context

# Load environment variables
load_dotenv()
logging.basicConfig(level=logging.WARNING)
TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 10000))
STATIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static", "miniapp"))

# Flask app
health_app = Flask(__name__, static_folder="../static")
application = (
    ApplicationBuilder().token(TOKEN).build()
)

@health_app.route("/healthz")
def healthz():
    try:
        from app.session_db import _client as _redis_client
        _redis_client.ping()
    except Exception:
        pass
    return jsonify(status="ok"), 200

@health_app.route("/miniapp/<path:filename>")
def serve_miniapp(filename):
    return send_from_directory(STATIC_DIR, filename)

@health_app.route("/")
def root():
    return redirect("/healthz")

# ---- Flask Webhook endpoint ----
@health_app.route("/telegram", methods=["POST"])
def telegram_webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    # PTB v20+:
    application.update_queue.put(update)
    return jsonify(status="ok")

# --- Telegram Handlers (unchanged) ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hello! I’m HappyBot, your friendly companion. Type /help to see what I can do.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start     – Begin chatting with HappyBot\n"
        "/help      – Show this help menu\n"
        "/checkin   – Schedule a weekly wellbeing poll\n"
        "/exercise  – Watch a short Tai Chi video\n"
        "/sticker   – Get an exercise sticker\n\n"
        "You can also send me a voice note and I’ll reply by text and voice!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    uid = update.effective_chat.id
    crisis_keywords = ["depressed", "hopeless", "suicidal", "kill myself"]
    if any(word in text.lower() for word in crisis_keywords):
        await update.message.reply_text(
            "I’m really sorry you’re feeling this way. "
            "If you need help right now, please call Samaritans of Singapore at 1800-221-4444 "
            "or visit https://www.sos.org.sg/."
        )
        return
    empathy_keywords = ["sad", "lonely", "down", "unhappy"]
    if any(word in text.lower() for word in empathy_keywords):
        await update.message.reply_text(
            "I understand it can be tough. I’m here for you—"
            "would you like to talk more or hear something uplifting?"
        )
        return
    ctx = detect_context(text)
    update_user_context(uid, ctx)
    prompt = format_prompt(ctx, text)
    reply = generate_response(prompt)
    await update.message.reply_text(reply)

# (leave your other handlers unchanged, e.g. handle_voice, checkin_command, poll_handler...)

# --- Register Handlers ---
application.add_handler(CommandHandler("start", start_command))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CommandHandler("checkin", checkin_command))
application.add_handler(CommandHandler("sticker", send_sticker))
application.add_handler(CommandHandler("exercise", send_exercise_video))
application.add_handler(MessageHandler(filters.VOICE, handle_voice))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
application.add_handler(PollHandler(poll_handler))

def main():
    # Set webhook at startup
    application.bot.delete_webhook()
    application.bot.set_webhook(url=f"{WEBHOOK_URL}/telegram")
    # Start Flask
    health_app.run(host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    main()

