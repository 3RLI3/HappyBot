import pytest
from app.utils import detect_context

@pytest.mark.parametrize("input_text,expected_context", [
    ("What should I cook today?", "daily_life"),
    ("I have a headache", "health_wellness"),
    ("I feel lonely", "emotional_support"),
    ("My phone is slow", "technology_help"),
    ("Tell me about local events", "local_culture"),
    ("Just chatting", "general_conversation"),
])
def test_detect_context(input_text, expected_context):
    assert detect_context(input_text) == expected_context