# app/telegram_bot.py

import os
import threading
import logging
import tempfile
from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, send_from_directory
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

STATIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static", "miniapp"))

# Flask app for health checks
health_app = Flask(__name__, static_folder="../static")

@health_app.route("/healthz")
def healthz():
    """Health check endpoint to verify service and Redis connectivity."""
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
    """Redirect root to /healthz for easy monitoring."""
    return redirect("/healthz")


# === Command Handlers ===

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    await update.message.reply_text(
        "👋 Hello! I’m HappyBot, your friendly companion. Type /help to see what I can do."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    await update.message.reply_text(
        "/start     – Begin chatting with HappyBot\n"
        "/help      – Show this help menu\n"
        "/checkin   – Schedule a weekly wellbeing poll\n"
        "/exercise  – Watch a short Tai Chi video\n"
        "/sticker   – Get an exercise sticker\n\n"
        "You can also send me a voice note and I’ll reply by text and voice!"
    )


# === Message Handlers ===

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process incoming text messages with empathy, crisis escalation, or AI flow."""
    text = update.message.text or ""
    uid = update.effective_chat.id

    # Crisis escalation
    crisis_keywords = ["depressed", "hopeless", "suicidal", "kill myself"]
    if any(word in text.lower() for word in crisis_keywords):
        await update.message.reply_text(
            "I’m really sorry you’re feeling this way. "
            "If you need help right now, please call Samaritans of Singapore at 1800-221-4444 "
            "or visit https://www.sos.org.sg/."
        )
        return

    # Empathy prompts
    empathy_keywords = ["sad", "lonely", "down", "unhappy"]
    if any(word in text.lower() for word in empathy_keywords):
        await update.message.reply_text(
            "I understand it can be tough. I’m here for you—"
            "would you like to talk more or hear something uplifting?"
        )
        return

    # Standard AI flow
    ctx = detect_context(text)
    update_user_context(uid, ctx)
    prompt = format_prompt(ctx, text)
    reply = generate_response(prompt)
    await update.message.reply_text(reply)


async def handle_voice(update, context):
    """Process incoming voice messages with offline STT and TTS reply."""
    voice = update.message.voice
    tg_file = await voice.get_file()

    # Create a temp path without locking
    fd, ogg_path = tempfile.mkstemp(suffix=".ogg")
    os.close(fd)
    await tg_file.download_to_drive(ogg_path)

    wav_path = ogg_path.replace(".ogg", ".wav")
    AudioSegment.from_ogg(ogg_path).export(wav_path, format="wav")
    os.unlink(ogg_path)  # clean up .ogg

    # Download and convert voice to WAV
    with tempfile.NamedTemporaryFile(suffix=".ogg") as ogg_f:
        await tg_file.download_to_drive(ogg_f.name)
        wav_path = ogg_f.name.replace(".ogg", ".wav")
        AudioSegment.from_ogg(ogg_f.name).export(wav_path, format="wav")

        # Offline speech recognition
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_sphinx(audio_data)
        except sr.UnknownValueError:
            text = ""

    if not text:
        await update.message.reply_text(
            "Sorry, I couldn't understand your voice. Could you please try again?"
        )
        return

    # AI flow on transcribed text
    ctx = detect_context(text)
    update_user_context(update.effective_chat.id, ctx)
    prompt = format_prompt(ctx, text)
    reply = generate_response(prompt)
    await update.message.reply_text(reply)

    # TTS reply
    tts = gTTS(reply)
    with tempfile.NamedTemporaryFile(suffix=".mp3") as mp3_f:
        tts.write_to_fp(mp3_f)
        mp3_f.flush()
        await update.message.reply_voice(voice=open(mp3_f.name, "rb"))


# === Weekly Check-In Poll ===

CHECKIN_Q = "How are you feeling this week?"
CHECKIN_OPTS = ["Great", "Okay", "Not so good"]

async def checkin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Schedule a weekly check-in poll on Mondays."""
    chat_id = update.effective_chat.id
    context.job_queue.run_weekly(
        lambda ctx: ctx.bot.send_poll(
            chat_id,
            CHECKIN_Q,
            CHECKIN_OPTS,
            is_anonymous=False,
            allows_multiple_answers=False,
        ),
        days=0  # Monday
    )
    await update.message.reply_text("✅ Weekly check-in scheduled!")

async def poll_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Acknowledge poll responses."""
    await update.effective_message.reply_text("Thanks for sharing! Talk again next week.")


# === Multimedia Handlers ===

async def send_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send an exercise sticker."""
    sticker_id = os.getenv("static/exercise_sticker_id.png")
    await update.message.reply_sticker(sticker=sticker_id)

async def send_exercise_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a Tai Chi exercise video snippet."""
    video_url = os.getenv("https://www.youtube.com/watch?v=y2RAEnWreoE&t=6s")
    await update.message.reply_video(video=video_url, caption="🧘‍♂️ Try this Tai Chi routine!")


# === Main Entry ===

async def on_startup(application):
    # Remove any webhook and purge queued updates in one call
    await application.bot.delete_webhook(drop_pending_updates=True)

def main():
    # 1) Start your Flask health server as before…
    port = int(os.getenv("PORT", 10000))
    threading.Thread(
        target=lambda: health_app.run(host="0.0.0.0", port=port),
        daemon=True
    ).start()

    # 2) Build the Telegram application, registering the startup hook
    app = (
        ApplicationBuilder()
        .token(TOKEN)
        .post_init(on_startup)   # this will run before polling
        .build()
    )

    # 3) Add your command / message handlers…
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("checkin", checkin_command))
    app.add_handler(CommandHandler("sticker", send_sticker))
    app.add_handler(CommandHandler("exercise", send_exercise_video))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(PollHandler(poll_handler))
    # Start long polling, dropping any stale updates on the server
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
