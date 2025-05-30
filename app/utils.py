# Intent Classification (Context Detection) - Simple Keyword-based Classifier to determine the conversational category from user input
import re
import logging

# Enhanced keyword mapping
CONTEXT_KEYWORDS = {
    "daily_life": ["cook", "cooking", "grocery", "medicine", "shopping", "weather", "laundry", "clean", "meal"],
    "health_wellness": ["exercise", "headache", "sleep", "wellness", "pain", "diet", "walk", "health", "hydrate"],
    "emotional_support": ["lonely", "sad", "depressed", "friends", "family", "anxious", "worried", "bored", "stressed"],
    "technology_help": ["phone", "video call", "zoom", "whatsapp", "alarm", "scam", "wifi", "reset", "slow", "computer", "tablet"],
    "local_culture": ["events", "places", "heritage", "museum", "history", "tv show", "drama", "hawker", "festival"],
}

def detect_context(user_input: str) -> str:
    """
    Determine conversational context from user input using keyword matching.
    Falls back to 'general_conversation' if no match is found.
    """
    ui = user_input.lower()
    for context, keywords in CONTEXT_KEYWORDS.items():
        for word in keywords:
            if re.search(rf'\b{re.escape(word)}\b', ui):
                logging.debug(f"Context detected: {context} (matched keyword: '{word}')")
                return context

    logging.info(f"No specific context detected for input: {user_input!r}")
    return "general_conversation"
