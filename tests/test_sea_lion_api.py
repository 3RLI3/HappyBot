import os
import pytest
from app import sea_lion_api

class DummyMessage:
    def __init__(self, content):
        self.content = content

class DummyChoice:
    def __init__(self, message):
        self.message = message

class DummyCompletion:
    def __init__(self, text):
        self.choices = [DummyChoice(DummyMessage(text))]

@pytest.fixture(autouse=True)
def set_api_key(monkeypatch):
    # Ensure API key and base_url are set
    monkeypatch.setenv('SEA_LION_API_KEY', 'test-key')
    monkeypatch.setenv('BASE_URL', 'https://api.sea-lion.ai/v1')
    yield


def test_generate_response(monkeypatch):
    captured_prompt = {}
    
    def fake_create(model, messages):
        # verify arguments
        assert model == "aisingapore/Gemma-SEA-LION-v3-9B-IT"
        assert isinstance(messages, list)
        captured_prompt['messages'] = messages
        return DummyCompletion("hello senior")

    # Monkey-patch the client
    monkeypatch.setattr(sea_lion_api.client.chat.completions, 'create', fake_create)

    response = sea_lion_api.generate_response("Test prompt")
    assert response == "hello senior"
    # Ensure prompt passed correctly
    assert captured_prompt['messages'][0]['content'] == "Test prompt"
