# Intent Classification (Context Detection) - Simple Keyword-based Classifier to determine the conversational category from user input
def detect_context(user_input: str) -> str:
    keywords = {
        "daily_life": ["cook", "medicine", "shopping", "weather"],
        "health_wellness": ["exercise", "headache", "sleep", "health", "pain"],
        "emotional_support": ["lonely", "sad", "friends", "family", "bored"],
        "technology_help": ["phone", "video call", "alarm", "scam", "slow"],
        "local_culture": ["events", "places", "history", "tv show", "drama"],
    }
    ui = user_input.lower()
    for ctx, words in keywords.items():
        if any(word in ui for word in words):
            return ctx
    return "general_conversation"