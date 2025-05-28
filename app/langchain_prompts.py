from langchain.prompts import PromptTemplate

prompt_templates = {
    "daily_life": PromptTemplate(
        template=(
            "You are a friendly assistant helping seniors with daily life tasks. "
            "Last time, we discussed similar tasks. Keep your responses clear and connected.\n\n"
            "Query: {query}\nResponse:"
        ),
        input_variables=["query"]
    ),
    "health_wellness": PromptTemplate(
        template=(
            "You are a friendly assistant helping seniors with daily life tasks. "
            "Last time, we discussed similar tasks. Keep your responses clear and connected.\n\n"
            "Query: {query}\nResponse:"
        ),
        input_variables=["query"]
    ),
    "emotional_support": PromptTemplate(
        template=(
            "You are a friendly assistant helping seniors with daily life tasks. "
            "Last time, we discussed similar tasks. Keep your responses clear and connected.\n\n"
            "Query: {query}\nResponse:"
        ),
        input_variables=["query"]
    ),
    "technology_help": PromptTemplate(
        template=(
            "You are a friendly assistant helping seniors with daily life tasks. "
            "Last time, we discussed similar tasks. Keep your responses clear and connected.\n\n"
            "Query: {query}\nResponse:"
        ),
        input_variables=["query"]
    ),
    "local_culture": PromptTemplate(
        template=(
            "You are a friendly assistant helping seniors with daily life tasks. "
            "Last time, we discussed similar tasks. Keep your responses clear and connected.\n\n"
            "Query: {query}\nResponse:"
        ),
        input_variables=["query"]
    ),
    "general_conversation": PromptTemplate(
        template=(
            "You are a friendly assistant helping seniors with daily life tasks. "
            "Last time, we discussed similar tasks. Keep your responses clear and connected.\n\n"
            "Query: {query}\nResponse:"
        ),
        input_variables=["query"]
    ),
}

def format_prompt(context, query):
    prompt_template = prompt_templates.get(context, prompt_templates["general_conversation"])
    return prompt_template.format(query=query)

