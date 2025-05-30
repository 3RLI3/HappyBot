import os
import asyncio
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
    filters,
    ContextTypes,
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

FLASK_PORT = int(os.getenv("FLASK_PORT", 10000))  # your miniapp + healthz
BOT_PORT = int(os.getenv("BOT_PORT", 8443))       # PTB webhook

STATIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static", "miniapp"))

# Flask app for health checks and webhook endpoint
health_app = Flask(__name__, static_folder="../static")

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

@health_app.route("/telegram", methods=["POST"])
def telegram_webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    asyncio.create_task(telegram_app.process_update(update))
    return jsonify(status="received")

# Command Handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "\U0001F44B Hello! I’m HappyBot, your friendly companion. Type /help to see what I can do."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start     – Begin chatting with HappyBot\n"
        "/help      – Show this help menu\n"
        "/checkin   – Schedule a weekly wellbeing poll\n"
        "/exercise  – Watch a short Tai Chi video\n"
        "/sticker   – Get an exercise sticker\n\n"
        "You can also send me a voice note and I’ll reply by text and voice!"
    )

# Message Handlers
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    uid = update.effective_chat.id

    crisis_keywords = ["depressed", "hopeless", "suicidal", "kill myself"]
    if any(word in text.lower() for word in crisis_keywords):
        await update.message.reply_text(
            "I’m really sorry you’re feeling this way. If you need help right now, "
            "please call Samaritans of Singapore at 1800-221-4444 or visit https://www.sos.org.sg/."
        )
        return

    empathy_keywords = ["sad", "lonely", "down", "unhappy"]
    if any(word in text.lower() for word in empathy_keywords):
        await update.message.reply_text(
            "I understand it can be tough. I’m here for you—would you like to talk more or hear something uplifting?"
        )
        return

    ctx = detect_context(text)
    update_user_context(uid, ctx)
    prompt = format_prompt(ctx, text)
    reply = generate_response(prompt)
    await update.message.reply_text(reply)

async def handle_voice(update, context):
    voice = update.message.voice
    tg_file = await voice.get_file()

    fd, ogg_path = tempfile.mkstemp(suffix=".ogg")
    os.close(fd)
    await tg_file.download_to_drive(ogg_path)

    wav_path = ogg_path.replace(".ogg", ".wav")
    AudioSegment.from_ogg(ogg_path).export(wav_path, format="wav")
    os.unlink(ogg_path)

    with tempfile.NamedTemporaryFile(suffix=".ogg") as ogg_f:
        await tg_file.download_to_drive(ogg_f.name)
        wav_path = ogg_f.name.replace(".ogg", ".wav")
        AudioSegment.from_ogg(ogg_f.name).export(wav_path, format="wav")

        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_sphinx(audio_data)
        except sr.UnknownValueError:
            text = ""

    if not text:
        await update.message.reply_text("Sorry, I couldn't understand your voice. Could you please try again?")
        return

    ctx = detect_context(text)
    update_user_context(update.effective_chat.id, ctx)
    prompt = format_prompt(ctx, text)
    reply = generate_response(prompt)
    await update.message.reply_text(reply)

    tts = gTTS(reply)
    with tempfile.NamedTemporaryFile(suffix=".mp3") as mp3_f:
        tts.write_to_fp(mp3_f)
        mp3_f.flush()
        await update.message.reply_voice(voice=open(mp3_f.name, "rb"))

CHECKIN_Q = "How are you feeling this week?"
CHECKIN_OPTS = ["Great", "Okay", "Not so good"]

async def checkin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    context.job_queue.run_weekly(
        lambda ctx: ctx.bot.send_poll(
            chat_id,
            CHECKIN_Q,
            CHECKIN_OPTS,
            is_anonymous=False,
            allows_multiple_answers=False,
        ),
        days=0
    )
    await update.message.reply_text("\u2705 Weekly check-in scheduled!")

async def poll_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text("Thanks for sharing! Talk again next week.")

async def send_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sticker_id = os.getenv("STICKER_ID")
    await update.message.reply_sticker(sticker=sticker_id)

async def send_exercise_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    video_url = os.getenv("EXERCISE_VIDEO_URL")
    await update.message.reply_video(video=video_url, caption="\U0001F9D8\u200D♂\ufe0f Try this Tai Chi routine!")

async def set_webhook():
    await telegram_app.bot.delete_webhook(drop_pending_updates=True)
    await telegram_app.bot.set_webhook(f"{WEBHOOK_URL}/telegram")

async def start_command(update, context):
    await update.message.reply_text("Hello! I'm your bot.")

def main():
    # Load environment variables
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g., https://yourdomain.com
    PORT = int(os.getenv("PORT", 8443))

    # Start Flask app in a separate thread
    threading.Thread(
        target=lambda: health_app.run(host="0.0.0.0", port=PORT),
        daemon=True
    ).start()

    # Create the Telegram application
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start_command))

    # Run the webhook
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="/telegram",
        webhook_url=f"{WEBHOOK_URL}/telegram"
    )

if __name__ == "__main__":
    main()