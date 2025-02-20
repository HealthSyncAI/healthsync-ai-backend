import os
import requests
from dotenv import load_dotenv

load_dotenv()


async def get_huggingface_response(user_input: str) -> str:
    api_key = os.getenv("HUGGINGFACE_API_KEY")
    if not api_key:
        return "Hugging Face API key not configured."

    API_URL = (
        "https://api-inference.huggingface.co/models/deepseek-ai/deepseek-llm-7b-chat"
    )
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        response = requests.post(API_URL, headers=headers, json={"inputs": user_input})
        response.raise_for_status()
        result = response.json()
        return result[0]["generated_text"]
    except requests.exceptions.RequestException as e:
        print(f"Error calling Hugging Face API: {e}")
        return "Sorry, I couldn't process that right now."
