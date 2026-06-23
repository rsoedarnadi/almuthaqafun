# test_tts.py
from dotenv import load_dotenv
load_dotenv()

import os
from openai import OpenAI

client = OpenAI(
    base_url=os.getenv("FANAR_BASE_URL"),
    api_key=os.getenv("FANAR_API_KEY")
)

response = client.audio.speech.create(
    model="Fanar-Aura-TTS-2",
    input="أهلاً وسهلاً! أنا راوي، مرشدك الثقافي.",
    voice="Hamad",
    response_format="mp3",
)

with open("greeting3.mp3", "wb") as f:
    f.write(response.read())

print("✓ Saved greeting3.mp3")