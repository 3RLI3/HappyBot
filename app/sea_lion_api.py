from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
SEA_LION_API_KEY = os.getenv("SEA_LION_API_KEY")
BASE_URL = "https://api.sea-lion.ai/v1"

client = OpenAI(
    api_key=SEA_LION_API_KEY,
    base_url=BASE_URL
)

def generate_response(prompt):
    completion = client.chat.completions.create(
        model="aisingapore/Gemma-SEA-LION-v3-9B-IT",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    return completion.choices[0].message.content.strip()
