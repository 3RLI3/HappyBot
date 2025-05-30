import os
import logging
import tempfile
import asyncio

from dotenv import load_dotenv
from aiohttp import web

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

# ── ENV / Logging ────────────────────────────────────────────
load_dotenv()
logging.basicConfig(level=logging.INFO)
TOKEN       = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")      # e.g. https://happybot-xusj.onrender.com
PORT        = int(os.getenv("PORT", "10000"))

# ── Build the PTB application ─────────────────────────────────
app = ApplicationBuilder().token(TOKEN).build()

# ── Telegram Handlers ─────────────────────────────────────────
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("[handler] start")
    await update.message.reply_text(
        "👋 Hello! I’m HappyBot, your friendly companion. Type /help to see what I can do."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("[handler] help")
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
    logging.info(f"[handler] message: {text!r}")

    # Crisis/empathy shortcuts omitted for brevity…
    ctx = detect_context(text)
    update_user_context(update.effective_chat.id, ctx)
    prompt = format_prompt(ctx, text)
    reply = generate_response(prompt)
    await update.message.reply_text(reply)

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    voice = update.message.voice
    tg_file = await voice.get_file()
    fd, ogg = tempfile.mkstemp(suffix=".ogg"); os.close(fd)
    await tg_file.download_to_drive(ogg)
    wav = ogg.replace(".ogg", ".wav")
    AudioSegment.from_ogg(ogg).export(wav, format="wav")
    os.unlink(ogg)

    recog = sr.Recognizer()
    with sr.AudioFile(wav) as src:
        audio = recog.record(src)
    try:
        text = recog.recognize_sphinx(audio)
    except sr.UnknownValueError:
        text = ""
    if not text:
        return await update.message.reply_text("Sorry, couldn't understand your voice.")
    ctx = detect_context(text)
    update_user_context(update.effective_chat.id, ctx)
    prompt = format_prompt(ctx, text)
    reply = generate_response(prompt)
    await update.message.reply_text(reply)
    tts = gTTS(reply)
    with tempfile.NamedTemporaryFile(suffix=".mp3") as mp3_f:
        tts.write_to_fp(mp3_f); mp3_f.flush()
        await update.message.reply_voice(voice=open(mp3_f.name, "rb"))

CHECKIN_Q = "How are you feeling this week?"
CHECKIN_OPTS = ["Great","Okay","Not so good"]
async def checkin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    context.job_queue.run_weekly(
        lambda ctx: ctx.bot.send_poll(chat_id, CHECKIN_Q, CHECKIN_OPTS,
                                      is_anonymous=False, allows_multiple_answers=False),
        days=0
    )
    await update.message.reply_text("✅ Weekly check-in scheduled!")

async def poll_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.poll.reply_text("Thanks for sharing!")

# ── Register handlers ───────────────────────────────────────────
app.add_handler(CommandHandler("start", start_command))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(MessageHandler(filters.VOICE, handle_voice))
app.add_handler(CommandHandler("checkin", checkin_command))
app.add_handler(PollHandler(poll_handler))

# ── Build an aiohttp Web App for both /telegram & /healthz ──────
web_app = app.build_webhook_app(
    path="/telegram",             # route for Telegram POSTs
    drop_pending_updates=True
)

async def health(request):
    return web.json_response({"status": "ok"})

web_app.router.add_get("/healthz", health)

# ── Entrypoint ─────────────────────────────────────────────────
if __name__ == "__main__":
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="/telegram",                       # the route
        webhook_url=f"{WEBHOOK_URL}/telegram",
        drop_pending_updates=True,
    )
