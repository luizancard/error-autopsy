import os
from datetime import datetime
from textwrap import shorten
import analytics as an
import database as db
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from google import genai
errors = db.load_data()
RESET = "\033[0m"
RED = "\033[91m"

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if api_key:
    client = genai.Client(api_key=api_key)
else:
    client = None


print(an.generate_web_insight(errors))