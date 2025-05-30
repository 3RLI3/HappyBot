import os
import threading 
import logging
import tempfile
import asyncio
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

# === Custom business logic ===
import speech_recognition as sr
from gtts import gTTS
from pydub import AudioSegment
from app.sea_lion_api import generate_response
from app.langchain_prompts import format_prompt
from app.utils import detect_context
from app.session_db import update_user_context

# === ENV & Logging ===
load_dotenv()
logging.basicConfig(level=logging.INFO)
TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")   # e.g. https://happybot-xusj.onrender.com
PORT = int(os.getenv("PORT", 10000))
STATIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static", "miniapp"))

# === Flask ===
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

# === Telegram Application (PTB v20+) ===
application = ApplicationBuilder().token(TOKEN).build()
application_is_ready = False
application_ready_lock = threading.Lock()

@health_app.before_first_request
def init_ptb_application():
    global application_is_ready
    with application_ready_lock:
        if not application_is_ready:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(application.initialize())
            loop.run_until_complete(application.start())
            application_is_ready = True

# === Telegram webhook endpoint ===
@health_app.route("/telegram", methods=["POST"])
def telegram_webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(application.process_update(update))
    return jsonify(status="ok")

# === Telegram handlers ===
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

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    voice = update.message.voice
    tg_file = await voice.get_file()
    fd, ogg_path = tempfile.mkstemp(suffix=".ogg")
    os.close(fd)
    await tg_file.download_to_drive(ogg_path)
    wav_path = ogg_path.replace(".ogg", ".wav")
    AudioSegment.from_ogg(ogg_path).export(wav_path, format="wav")
    os.unlink(ogg_path)
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
    await update.message.reply_text("✅ Weekly check-in scheduled!")

async def poll_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text("Thanks for sharing! Talk again next week.")

async def send_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sticker_id = os.getenv("STICKER_ID")
    await update.message.reply_sticker(sticker=sticker_id)

async def send_exercise_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    video_url = os.getenv("EXERCISE_VIDEO_URL")
    await update.message.reply_video(video=video_url, caption="🧘‍♂️ Try this Tai Chi routine!")

# === Register handlers ===
application.add_handler(CommandHandler("start", start_command))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CommandHandler("checkin", checkin_command))
application.add_handler(CommandHandler("sticker", send_sticker))
application.add_handler(CommandHandler("exercise", send_exercise_video))
application.add_handler(MessageHandler(filters.VOICE, handle_voice))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
application.add_handler(PollHandler(poll_handler))

# === Set webhook on startup (for Gunicorn) ===
async def set_webhook():
    await application.bot.delete_webhook()
    await application.bot.set_webhook(url=f"{WEBHOOK_URL}/telegram")

# For Gunicorn: set webhook once when process starts.
if os.getenv("RENDER", "").lower() == "true" or os.getenv("GUNICORN_CMD_ARGS"):
    # Only set webhook if running in production (Render, Gunicorn, etc)
    asyncio.run(set_webhook())

# For local dev, uncomment below:
# if __name__ == "__main__":
#     asyncio.run(set_webhook())
#     health_app.run(host="0.0.0.0", port=PORT)
