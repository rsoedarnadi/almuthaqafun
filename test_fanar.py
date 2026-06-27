import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("FANAR_API_KEY")
base_url = os.getenv("FANAR_BASE_URL")
model = os.getenv("FANAR_MODEL")

print("FANAR_API_KEY exists:", bool(api_key))
print("FANAR_BASE_URL:", base_url)
print("FANAR_MODEL:", model)

if not api_key or not base_url:
    raise RuntimeError("Missing FANAR_API_KEY or FANAR_BASE_URL in .env")

client = OpenAI(
    api_key=api_key,
    base_url=base_url,
)

response = client.chat.completions.create(
    model=model,
    messages=[
        {
            "role": "system",
            "content": "You are Maryam, a helpful Qatari cultural guide."
        },
        {
            "role": "user",
            "content": "Say hello in Arabic and English."
        }
    ],
    max_tokens=100,
)

print("\n========== FANAR RESPONSE ==========")
print(response.choices[0].message.content)
print("====================================")