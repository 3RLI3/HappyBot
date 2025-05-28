# Intent Classification (Context Detection) - Simple Keyword-based Classifier to determine the conversational category from user input
def detect_context(user_input):
    context_keywords = {
        "daily_life": ["cook", "medicine", "shopping", "weather"],
        "health_wellness": ["exercise", "headache", "sleep", "health", "pain"],
        "emotional_support": ["lonely", "sad", "friends", "family", "bored"],
        "technology_help": ["phone", "video call", "alarm", "scam", "slow"],
        "local_culture": ["events", "places", "history", "TV show", "drama"],
    }
    
    for context, keywords in context_keywords.items():
        if any(keyword.lower() in user_input.lower() for keyword in keywords):
            return context
    
    return "general_conversation"


def cleanup_old_sessions(days_old=30):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM user_sessions
        WHERE last_interaction < datetime('now', ?)
    ''', (f'-{days_old} days',))
    conn.commit()
    conn.close()
