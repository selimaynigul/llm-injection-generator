import openai
import os
from dotenv import load_dotenv

load_dotenv()

# OPENAI_API_KEY'i ortam değişkeninden alabilir ya da doğrudan buraya yazabilirsin (güvenli değil)
openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_payload(context):
    prompt = f"""
You are an expert in web security testing. Your task is to craft a proof-of-concept XSS payload based on the structure of the target website. 

Target page details:
{context}

Generate exactly 15 **minimal and well-formed** working XSS payloads that would be most likely to succeed, assuming a vulnerable context.
Write them in a single line, separated by newline. No explanation, no line breaks, no bullet points. Just one single string.

Respond with **only** the payloads string.
"""


    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",  # dilersen gpt-4 seçebilirsin
            messages=[
                {"role": "system", "content": "You are a penetration tester."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.7
        )

        return response['choices'][0]['message']['content'].strip()

    except Exception as e:
        return f"[!] Error generating payload: {e}"
