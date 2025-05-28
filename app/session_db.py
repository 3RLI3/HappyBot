import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'sessions.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_sessions (
            chat_id INTEGER PRIMARY KEY,
            context TEXT,
            last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def update_user_context(chat_id, context):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO user_sessions (chat_id, context, last_interaction)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(chat_id) DO UPDATE SET
        context=excluded.context,
        last_interaction=CURRENT_TIMESTAMP
    ''', (chat_id, context))
    conn.commit()
    conn.close()

def get_user_context(chat_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT context FROM user_sessions WHERE chat_id = ?', (chat_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else "general_conversation"
