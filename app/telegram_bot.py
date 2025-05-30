import os
import logging
import tempfile
import asyncio
import datetime
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    PollAnswerHandler,
    ContextTypes,
    filters,
)

import speech_recognition as sr
from gtts import gTTS
from pydub import AudioSegment

from app.sea_lion_api import generate_response
from app.langchain_prompts import format_prompt
from app.utils import detect_context
from app.session_db import (
    update_user_context,
    append_user_history,
    get_user_context,
)

# ── ENV / Logging ────────────────────────────────────────────
load_dotenv()
logging.basicConfig(level=logging.INFO)
TOKEN       = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")      # e.g. https://happybot-xusj.onrender.com
PORT        = int(os.getenv("PORT", "10000"))

# ── Build the PTB application ─────────────────────────────────
app = ApplicationBuilder().token(TOKEN).build()

@app.route("/miniapp/<path:filename>")
def serve_miniapp(filename):
    return send_from_directory(STATIC_DIR, filename)

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

    # Crisis support
    if any(word in user_text.lower() for word in ["suicidal", "hopeless", "depressed", "end it all"]):
        await update.message.reply_text(
            "💔 I'm truly sorry you're feeling this way. Please know that you're not alone.\n\n"
            "It takes strength to express what you're going through, and I’m here for you "
            " — to listen, support, or simply be present. You matter, and your feelings are valid.\n\n"
            "If things feel overwhelming, I encourage you to talk to someone."
            "You can reach out to Samaritans of Singapore at 📞 1800-221-4444 or visit 🌐 sos.org.sg, "
            "They’re available 24/7 with trained volunteers who care and are ready to listen without judgment.\n\n"
            "In the meantime, if you'd like, I can share a calming exercise or just chat with you — no pressure at all."
            "🤝 You're not alone in this. 🤝",
            parse_mode="Markdown"
        )
        return

    # Empathy support
    if any(word in user_text.lower() for word in ["sad", "lonely", "anxious", "unhappy", "tired"]):
        await update.message.reply_text(
            "🌧️ I hear you. It’s okay to feel this way sometimes. "
            "I’m here to chat, share something uplifting, or just listen. 💙\n\n"
            "Would you like a motivational quote, a breathing exercise, or a fun fact?"
        )
        return

    # Context-based response
    ctx = detect_context(user_text)
    logging.info(f"No specific context detected for input: {user_text!r}") if ctx == "general_conversation" else None
    update_user_context(user_id, ctx)
    append_user_history(user_id, f"User: {user_text}")
    
    try:
        prompt = format_prompt(ctx, user_text, user_id=user_id)
        reply = generate_response(prompt)
    except Exception:
        logging.exception("generate_response failed")
        reply = "😔 Oops! Something went wrong while generating my response. Please try again later."

    append_user_history(user_id, f"Bot: {reply}")
    await update.message.reply_text(f"💬 {reply}")


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    voice = update.message.voice
    tg_file = await voice.get_file()

    # Step 1: Save .ogg file
    fd, ogg_path = tempfile.mkstemp(suffix=".ogg"); os.close(fd)
    await tg_file.download_to_drive(ogg_path)

    # Step 2: Convert to .wav and normalize
    wav_path = ogg_path.replace(".ogg", ".wav")
    audio = AudioSegment.from_ogg(ogg_path)
    normalized = audio.set_frame_rate(16000).set_channels(1).normalize()
    normalized.export(wav_path, format="wav")
    os.unlink(ogg_path)

    # Step 3: Recognize speech
    recog = sr.Recognizer()
    with sr.AudioFile(wav_path) as src:
        audio_data = recog.record(src)

    try:
        text = recog.recognize_sphinx(audio_data)
    except sr.UnknownValueError:
        text = ""
    except sr.RequestError as e:
        logging.error(f"Sphinx error: {e}")
        text = ""

    os.unlink(wav_path)

    if not text:
        return await update.message.reply_text("😕 I couldn’t understand your voice clearly. Try speaking more slowly or clearly.")

    # Step 4: Generate and reply
    ctx = detect_context(text)
    update_user_context(update.effective_chat.id, ctx)
    reply = generate_response(user_text, context=context_tag, user_id=user_id)

    await update.message.reply_text(reply)
    tts = gTTS(reply)
    with tempfile.NamedTemporaryFile(suffix=".mp3") as mp3_f:
        tts.write_to_fp(mp3_f); mp3_f.flush()
        await update.message.reply_voice(voice=open(mp3_f.name, "rb"))

CHECKIN_Q = "How are you feeling this week?"
CHECKIN_OPTS = ["Great","Okay","Not so good"]

async def checkin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_first_name = update.effective_user.first_name or "there"

    try:
        context.job_queue.run_weekly(
            callback=lambda ctx: ctx.bot.send_poll(
                chat_id=chat_id,
                question="🧠 *Weekly Check-In*\n\nHow are you feeling this week?",
                options=["😊 Great", "😐 Okay", "😔 Not so good"],
                is_anonymous=False,
                allows_multiple_answers=False,
                parse_mode="Markdown"
            ),
            time=datetime.time(hour=9, minute=0),  # Every Monday at 9:00 AM (server time)
            days=(0,),  # 0 = Monday
            name=f"checkin_{chat_id}",
            chat_id=chat_id
        )

        await update.message.reply_text(
            f"✅ Got it, {user_first_name}!\n\nI’ve scheduled a gentle weekly check-in "
            f"for every *Monday at 9AM*. You'll get a quick wellness poll in this chat. "
            f"You can always cancel it with /cancelcheckin.",
            parse_mode="Markdown"
        )

    except Exception as e:
        logging.error(f"[checkin_command] Failed to schedule check-in: {e}")
        await update.message.reply_text(
            "⚠️ Sorry, something went wrong while setting up your check-in. Please try again later."
        )

async def handle_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.poll_answer.user.id
    first_name = update.poll_answer.user.first_name or "there"
    selected_option = update.poll_answer.option_ids[0] if update.poll_answer.option_ids else None

    if selected_option is not None:
        option_text = ["Great 😊", "Okay 😐", "Not so good 😔"][selected_option]
        logging.info(f"[poll answer] {first_name} selected: {option_text}")

        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"💬 Thanks for sharing, {first_name}! You said: *{option_text}*.\n"
                     f"Feel free to check in with me anytime 💛",
                parse_mode="Markdown"
            )
        except Exception as e:
            logging.warning(f"Couldn't send message to user {user_id}: {e}")
    else:
        logging.warning(f"[poll answer] No option selected by user {user_id}")

# ── Register handlers ───────────────────────────────────────────
app.add_handler(CommandHandler("start", start_command))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(MessageHandler(filters.VOICE, handle_voice))
app.add_handler(CommandHandler("checkin", checkin_command))
app.add_handler(PollAnswerHandler(handle_poll_answer))

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
