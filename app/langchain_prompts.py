from langchain.prompts import PromptTemplate
from app.session_db import get_user_history

prompt_templates = {
    "daily_life": PromptTemplate(
        template=(
            "You are a kind, patient assistant for elderly users.\n"
            "Refer to past chats if helpful to keep context.\n\n"
            "Conversation history:\n{history}\n\n"
            "User task:\n{query}\n\n"
            "Response:"
        ),
        input_variables=["history", "query"]
    ),
    "health_wellness": PromptTemplate(
        template=(
            "You are a caring and knowledgeable assistant who helps elderly users understand and manage their health and wellness.\n"
            "Speak in a gentle, reassuring tone using simple, clear language.\n\n"
            "{history}\n"  # Recent context, if available

            "User: {query}\n"
            "Helpful response:"
        ),
        input_variables=["history", "query"]
    ),  
    "emotional_support": PromptTemplate(
        template=(
            "You are a compassionate, gentle companion helping elderly users cope with emotional challenges.\n"
            "Respond with kindness, empathy, and warmth. Speak clearly and use simple, comforting language.\n\n"
            "{history}\n"
            "User: {query}\n"
            "Supportive response:"
        ),
        input_variables=["history", "query"]
    ),
    "technology_help": PromptTemplate(
        template=(
            "You are a calm and patient assistant helping elderly users with technology.\n"
            "Use simple words, guide step-by-step, and reassure users when things are unclear.\n\n"
            "{history}\n"
            "User: {query}\n"
            "Helpful response:"
        ),
        input_variables=["history", "query"]
    ),
    "local_culture": PromptTemplate(
        template=(
            "You are a warm and engaging assistant helping seniors explore their local culture.\n"
            "Share relatable stories, traditions, and events in an uplifting tone.\n\n"
            "{history}\n"
            "User: {query}\n"
            "Culturally relevant response:"
        ),
        input_variables=["history", "query"]
    ),
    "general_conversation": PromptTemplate(
        template=(
            "You are a friendly companion having a light, natural conversation with an elderly user.\n"
            "Keep it cheerful, thoughtful, and easy to follow. Use plain language and stay on familiar topics.\n\n"
            "{history}\n"
            "User: {query}\n"
            "Chatty response:"
        ),
        input_variables=["history", "query"]
    )
}

def format_prompt(context, query, user_id=None):
    prompt_template = prompt_templates.get(context, prompt_templates["general_conversation"])

    history_lines = get_user_history(user_id) if user_id else []
    truncated_history = "\n".join(history_lines[-4:])  # last 4 messages

    return prompt_template.format(
        history=f"Recent conversation:\n{truncated_history}" if truncated_history else "This is the start of the conversation."
    )
    