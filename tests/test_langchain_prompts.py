from app.langchain_prompts import format_prompt


def test_format_prompt_includes_query():
    query = "Help me with exercise"
    prompt = format_prompt("health_wellness", query)
    assert "Query: Help me with exercise" in prompt
    assert prompt.startswith("You're a caring companion")  or "health advice" in prompt
