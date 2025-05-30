import os
import requests
import logging
from dotenv import load_dotenv
from app.langchain_prompts import format_prompt
from app.session_db import append_user_history

load_dotenv()

API_KEY = os.getenv("SEA_LION_API_KEY")
BASE_URL = "https://api.sea-lion.ai/v1/chat/completions"
MODEL_NAME = "aisingapore/Gemma-SEA-LION-v3-9B-IT"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def generate_response(query: str, context: str = "general_conversation", user_id: int = None) -> str:
    """
    Generate a model response using Sea-Lion API with optional memory and context.

    Args:
        query (str): The user's input.
        context (str): Context label for prompt formatting.
        user_id (int, optional): User ID to retrieve conversation history.

    Returns:
        str: The LLM-generated response.
    """
    prompt = format_prompt(context, query, user_id=user_id)

    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }

    try:
        response = requests.post(BASE_URL, headers=HEADERS, json=payload, timeout=10)
        response.raise_for_status()
        result = response.json()

        reply = result["choices"][0]["message"]["content"].strip()
        if user_id:
            append_user_history(user_id, f"User: {query}")
            append_user_history(user_id, f"Bot: {reply}")

        return reply

    except requests.RequestException as e:
        logging.exception("Sea-Lion API request failed")
        return "⚠️ Sorry, I'm having trouble connecting to the assistant. Please try again shortly."
    except (KeyError, IndexError):
        logging.exception("Unexpected response format from Sea-Lion API")
        return "⚠️ I didn't understand that. Can you try rephrasing?"