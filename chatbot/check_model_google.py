from chatbot.config import config as app_config

import google.genai as genai


client = genai.Client(api_key=app_config.GOOGLE_API_KEY)

models = client.models.list()

for m in models:
    print(m.name)

try:
    client.models.generate_content(
        model="gemini-3-pro-preview",
        contents="ping",
        config=genai.types.GenerateContentConfig(max_output_tokens=1)
    )
    print("Model is now available!")
except Exception as e:
    if "quota" in str(e).lower() or "exceeded" in str(e).lower():
        print("Still not available (quota = 0)")
    else:
        print("Other error:", e)
