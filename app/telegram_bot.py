import os
import logging
import tempfile
import asyncio

from dotenv import load_dotenv

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    PollHandler,
    ContextTypes,
    filters,
)

import whisper 
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
        "🌞 *Welcome to HappyBot!*\n\n"
        "I'm your friendly companion for wellbeing, relaxation, and a little bit of fun. "
        "Type /help to see everything I can do — or just say hello!",
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("[handler] help")
    await update.message.reply_text(
        "📘 *Here’s what I can do:*\n\n"
        "👉 `/start` – Begin a fresh conversation with HappyBot\n"
        "❓ `/help` – Show this help menu\n"
        "🗳️ `/checkin` – Schedule a weekly wellbeing check-in\n"
        "🎥 `/exercise` – Watch a short Tai Chi video to relax\n"
        "🌟 `/sticker` – Receive a cheerful sticker reward\n"
        "🎙️ *Send a voice note* – I’ll transcribe and respond in text + voice\n\n"
        "💬 You can also just type messages like:\n"
        "_“I’m feeling down”_ or _“Tell me something uplifting”_\n"
        "and I’ll be here to support you 💖",
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text or ""
    user_id = update.effective_chat.id
    logging.info(f"[handler] message: {user_text!r}")

    # Simple keyword-based emotional shortcuts
    crisis_words = ["suicidal", "hopeless", "depressed", "end it all"]
    if any(word in user_text.lower() for word in crisis_words):
        await update.message.reply_text(
            "💔 I'm really sorry you're feeling this way. You're not alone.\n\n"
            "Please consider calling *Samaritans of Singapore* at 📞 *1800-221-4444*, "
            "or visit https://www.sos.org.sg for help. They’re available 24/7.",
            parse_mode="Markdown"
        )
        return

    empathy_words = ["sad", "lonely", "anxious", "unhappy", "tired"]
    if any(word in user_text.lower() for word in empathy_words):
        await update.message.reply_text(
            "🌧️ I hear you. It’s okay to feel this way sometimes. "
            "I’m here to chat, share something uplifting, or just listen. 💙\n\n"
            "Would you like a motivational quote, a breathing exercise, or a fun fact?"
        )
        return

    # Context-aware AI reply
    context_tag = detect_context(user_text)
    update_user_context(user_id, context_tag)
    prompt = format_prompt(context_tag, user_text)

    try:
        reply = generate_response(prompt)
    except Exception as e:
        logging.exception("generate_response failed")
        reply = "Oops! Something went wrong while generating my response. Please try again later."

    await update.message.reply_text(f"💬 {reply}")

whisper_model = whisper.load_model("base")

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    voice = update.message.voice
    tg_file = await voice.get_file()

    # Save incoming OGG file
    fd, ogg = tempfile.mkstemp(suffix=".ogg"); os.close(fd)
    await tg_file.download_to_drive(ogg)

    # Convert to WAV (or MP3/MP4/M4A supported by Whisper)
    wav = ogg.replace(".ogg", ".wav")
    AudioSegment.from_ogg(ogg).export(wav, format="wav")
    os.unlink(ogg)

    try:
        result = whisper_model.transcribe(wav)
        text = result.get("text", "").strip()
    except Exception as e:
        logging.exception("Whisper transcription failed")
        text = ""

    os.unlink(wav)

    if not text:
        return await update.message.reply_text("Sorry, I couldn't understand your voice. Could you please try again?")

    ctx = detect_context(text)
    update_user_context(update.effective_chat.id, ctx)
    prompt = format_prompt(ctx, text)
    reply = generate_response(prompt)

    await update.message.reply_text(reply)

    # TTS reply
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

# ── Entrypoint ─────────────────────────────────────────────────
if __name__ == "__main__":
    # app, not application
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="/telegram",
        webhook_url=f"{WEBHOOK_URL}/telegram",
        drop_pending_updates=True,
    )
