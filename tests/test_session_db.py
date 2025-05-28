import sqlite3
import os
import pytest
import tempfile

import app.session_db as session_db

@pytest.fixture(autouse=True)
def setup_tmp_db(monkeypatch, tmp_path):
    tmpfile = tmp_path / "test_sessions.db"
    monkeypatch.setattr(session_db, 'DB_PATH', str(tmpfile))
    session_db.init_db()
    return str(tmpfile)


def test_get_context_default():
    # No entry yet, should return general_conversation
    assert session_db.get_user_context(9999) == "general_conversation"


def test_update_and_get_context():
    chat_id = 1001
    session_db.update_user_context(chat_id, "daily_life")
    assert session_db.get_user_context(chat_id) == "daily_life"
    # Update again
    session_db.update_user_context(chat_id, "health_wellness")
    assert session_db.get_user_context(chat_id) == "health_wellness"
