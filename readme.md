## GPT Advisor Companion Bot

A Generative AI–Powered Telegram Companion Bot for Lonely Seniors in Singapore, leveraging the Sea‑Lion open‑source LLM via API and LangChain for context‑aware, empathetic conversations.

# 📖 Overview

GPT Advisor is a lightweight, scalable Python application that integrates with Telegram to provide senior users with:

Friendly, engaging conversations for emotional support.

Practical daily‑life guidance (health tips, simple recipes, reminders).

Technology assistance (step‑by‑step instructions).

Local recommendations (community events, cultural facts).

Powered by the Sea‑Lion API (model: aisingapore/Gemma-SEA-LION-v3-9B-IT) and LangChain prompt templates, the bot detects conversational context and tailors responses for maximum clarity and warmth.

# 🚀 Features

Context Detection: Classifies user queries into categories (e.g., Daily Life, Health, Emotional Support) using keyword‑based or ML‑based intent detection.

Prompt Engineering: Uses LangChain to format rich, context‑specific prompts for the LLM.

Sea‑Lion API Integration: Fetches responses from a local‑style open‑source LLM via HTTPS.

Session Management: Persists user context in an SQLite database (sessions.db) for continuity across chats.

Test Suite: Comprehensive pytest tests for utilities, session storage, prompt formatting, and API integration.

# 🔧 Architecture & Directory Structure

project_root/
├── app/
│   ├── __init__.py            # Package initializer
│   ├── telegram_bot.py        # Entry point and message handler
│   ├── sea_lion_api.py        # Sea‑Lion API wrapper
│   ├── langchain_prompts.py   # Contextual PromptTemplate definitions
│   ├── utils.py               # Context detection utilities
│   └── session_db.py          # SQLite session management
│
├── tests/                     # pytest test modules
│   ├── __init__.py
│   ├── test_utils.py
│   ├── test_session_db.py
│   ├── test_langchain_prompts.py
│   └── test_sea_lion_api.py
│
├── models/                    # (Optional) local Sea‑Lion model files
├── .env                       # Environment variables (Telegram & API keys)
├── requirements.txt           # Python dependencies
└── README.md                  # This documentation

# 🛠 Prerequisites

Python 3.8+

Telegram Bot Token (via BotFather)

Sea‑Lion API Key (sign up at https://sea-lion.ai)

# ⚙️ Installation

Clone the repo
```bash
git clone https://github.com/your-org/gpt-advisor-bot.git
cd gpt-advisor-bot
```

Create & activate virtual environment
```bash
python -m venv venv
source venv/bin/activate    # Linux/macOS
venv\Scripts\activate     # Windows
```

Install dependencies
```bash
pip install -r requirements.txt
```

Create .env file in project root:
```bash
TELEGRAM_TOKEN=<your-telegram-bot-token>
SEA_LION_API_KEY=<your-sea-lion-api-key>
```

# ▶️ Usage

Initialize the database (creates sessions.db):
```bash
python -c "from app.session_db import init_db; init_db()"
```
Run the bot:
```bash
python -m app.telegram_bot
```
Chat on Telegram:
```bash
Search for your bot’s username and send messages.
```

The bot auto‑detects context, formats prompts, and replies with AI‑generated responses.

# 🧪 Testing

Run all tests with pytest:
```bash
pytest --maxfail=1 --disable-warnings -q
```
Test coverage includes:
- Context detection (utils.detect_context)

- Session management (session_db)

- Prompt formatting (langchain_prompts.format_prompt)

- API integration (sea_lion_api.generate_response)

# 🤝 Contributing

Fork the repository and create a feature branch.

Write clear, concise code and documentation.

Add tests for new features or bug fixes.

Submit a pull request and link any relevant issues.

# 📜 License

This project is open‑source under the MIT License.

###      Built with ❤️ in Singapore       ###

