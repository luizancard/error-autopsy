import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

print(f"API Key found: {'Yes' if api_key else 'No'}")

if api_key:
    try:
        client = genai.Client(api_key=api_key)
        print("Client initialized.")
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Say 'Hello' if you can hear me.",
        )
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
else:
    print("Skipping client init.")
