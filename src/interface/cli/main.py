import os
from datetime import datetime

import analytics as anl
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


def view_database(data):
    if not data:
        print("\nDataBase is empty.")
    else:
        print("\n" + "-" * 97)
        header = f"| {'ID':<3} | {'Date':<10} | {'Subject':<12} | {'Topic':<15} | {'Type':<18} | {'Note':<20} |"
        print(BOLD + header + RESET)
        print("-" * 97)

        for row in data:
            print(
                f"| {row['id']:<3} | {row['date']:<10} | {row['subject']:<12} | {row['topic']:<15} | {row['type']:<18} | {row['description']:<20} |"
            )

        print("-" * 97 + "\n")


def main():
    errors = db.load_data()

    while True:
        print("\nError autopsy CLI")
        print("1. Log New Error")
        print("2. View error database")
        print("3. Analytics Hub")
        print("4. Delete database")
        print("5. Exit")

        option = input("Choose an option: ")

        if option == "1":
            register_error(errors)
        elif option == "2":
            view_database(errors)
        elif option == "3":
            while True:
                print("\nAnalytics Hub")
                print("1. View Graphs")
                print("2. Analyze my Patterns (AI)")
                print("3. Quick Summary (text)")
                print("4. Back to the Main Menu")
                sub_option = input("\nChoose analysis type: ")

                if sub_option == "1":
                    anl.create_graphs(errors)
                elif sub_option == "2":
                    anl.analyze_patterns(errors)
                elif sub_option == "3":
                    anl.quick_summary(errors)
                elif sub_option == "4":
                    break
                else:
                    print("Invalid option.")

        elif option == "4":
            del_confirmation = input(
                '\nType "Confirm" to confirm you want to delete your previus DataBase: \n'
            )
            if del_confirmation == "Confirm":
                db.delete_database(errors)
            else:
                print("\nConfirmation incomplete. DataBase was NOT deleted")
        elif option == "5":
            print("Goodbye!")
            break

        else:
            print("\nInvalid Option")


if __name__ == "__main__":
    main()
