from telegram.ext import ApplicationBuilder, MessageHandler, filters
from sea_lion_api import generate_response
from langchain_prompts import format_prompt
from utils import detect_context
from session_db import init_db, update_user_context, get_user_context
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

async def handle_message(update, context):
    user_input = update.message.text
    chat_id = update.message.chat_id

    # Retrieve previous context (if necessary)
    last_context = get_user_context(chat_id)

    # Detect new context based on the current message
    detected_context = detect_context(user_input)

    # Update session with new context
    update_user_context(chat_id, detected_context)

    # Format prompt using current context
    formatted_prompt = format_prompt(detected_context, user_input)

    # Generate and send response
    response = generate_response(formatted_prompt)
    await update.message.reply_text(response)

def main():
    # Initialize DB when bot starts
    init_db()

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()


