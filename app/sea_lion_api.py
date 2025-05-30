import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("SEA_LION_API_KEY")
BASE_URL = "https://api.sea-lion.ai/v1/chat/completions"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

def generate_response(prompt: str) -> str:
    payload = {
        "model": "aisingapore/Gemma-SEA-LION-v3-9B-IT",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    resp = requests.post(BASE_URL, json=payload, headers=HEADERS)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"].strip()
