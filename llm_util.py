import openai

# OPENAI_API_KEY'i ortam değişkeninden alabilir ya da doğrudan buraya yazabilirsin (güvenli değil)
openai.api_key = "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"  # güvenli kullanım için .env dosyasından alınabilir

def generate_payload(context):
    prompt = f"""
You are an expert in web security testing. Your task is to craft a proof-of-concept XSS payload based on the structure of the target website. 

Target page details:
{context}

Generate exactly twenty minimal working XSS payload that would be most likely to succeed, assuming a vulnerable context.

Respond with only the payload string. No explanation.
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # dilersen gpt-4 seçebilirsin
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
