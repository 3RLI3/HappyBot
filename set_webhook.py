#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()

TOKEN       = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g. https://happybot-xusj.onrender.com

bot = Bot(token=TOKEN)

# Delete any existing webhook and clear pending updates
bot.delete_webhook(drop_pending_updates=True)
print("✅ Old webhook deleted, backlog cleared.")

# Set the new webhook
bot.set_webhook(f"{WEBHOOK_URL}/telegram")
print(f"✅ Webhook set to {WEBHOOK_URL}/telegram")
