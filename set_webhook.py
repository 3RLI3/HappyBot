# set_webhook.py
import asyncio
import os
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

async def main():
    bot = Bot(token=TOKEN)
    await bot.delete_webhook(drop_pending_updates=True)
    print("✅ Old webhook deleted, backlog cleared.")
    await bot.set_webhook(url=f"{WEBHOOK_URL}/telegram")
    print(f"✅ Webhook set to {WEBHOOK_URL}/telegram")

if __name__ == "__main__":
    asyncio.run(main())

