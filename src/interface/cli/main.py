import os
from datetime import datetime

import database as db
from dotenv import load_dotenv
from google import genai

BOLD = "\033[1m"
RESET = "\033[0m"
RED = "\033[91m"

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if api_key:
    client = genai.Client(api_key=api_key)
else:
    client = None


file_bank = "error_log.json"

error_types = {
    "1": "Content Gap",
    "2": "Attention detail",
    "3": "Time management",
    "4": "Fatigue",
    "5": "Interpretation",
}


def register_error(error_list):
    try:
        subject = input("\nEnter the subject: ").strip()
        topic = input("\nEnter the subject topic: ").strip()
        description = input("\nEnter a description (optional): ").strip()

        # Validate date input
        while True:
            date = input("\nEnter the exam date (DD-MM-YYYY): ").strip()
            if date == "":
                final_date = datetime.now(tz=None).strftime("%d-%m-%Y")
                break
            try:
                datetime.strptime(date, "%d-%m-%Y")
                final_date = date
                break
            except ValueError:
                print("Invalid date format. Please use DD-MM-YYYY.")

        print("\nSelect the error type:")

        for code, name in error_types.items():
            print(f"[{code}]: {name}")

        while True:
            choice = input("\nOption number: ")
            if choice in error_types:
                error_name = error_types[choice]
                break
            else:
                print("\nInvalid option. Try again.")
            # dictionary for the mistakes
        new_error = {
            "id": len(error_list) + 1,
            "date": final_date,
            "subject": subject,
            "topic": topic,
            "description": description,
            "type": error_name,
        }
        # adding list and
        error_list.append(new_error)
        db.save_data(error_list)

    except ValueError:
        print("\nInvalid Input")
