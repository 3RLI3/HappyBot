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

load_dotenv()
logging.basicConfig(level=logging.WARNING)
TOKEN = os.getenv("TELEGRAM_TOKEN")

health_app = Flask(__name__)

@health_app.route("/healthz")
def healthz():
    try:
        from app.session_db import _client as _redis_client
        _redis_client.ping()
        return jsonify(status="ok"), 200
    except Exception:
        return jsonify(status="ok"), 200

@health_app.route("/")
def root():
    return redirect("/healthz")

def run_health_server():
    health_app.run(host="0.0.0.0", port=8000)

async def handle_message(update, context):
    user_input = update.message.text
    chat_id = update.message.chat_id
    detected = detect_context(user_input)
    update_user_context(chat_id, detected)
    prompt = format_prompt(detected, user_input)
    resp = generate_response(prompt)
    await update.message.reply_text(resp)

def main():
    threading.Thread(target=run_health_server, daemon=True).start()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()

