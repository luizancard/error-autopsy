import json
import os
from datetime import datetime

BOLD = "\033[1m"
RESET = "\033[0m"
RED = "\033[91m"

file_bank = "error_log.json"

error_types = {
    "1": "Content Gap",
    "2": "Attention detail",
    "3": "Time management",
    "4": "Fatigue",
    "5": "Interpretation",
}


def load_data():
    if not os.path.exists(file_bank):  # in case the file does not exist
        return []
    with open(
        file_bank, "r", encoding="utf-8"
    ) as file:  # reading file (accepts accents)
        return json.load(file)


def save_data(data):
    with open(file_bank, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)
    print("\nSaved succesfully!")


def register_error(error_list):
    try:
        subject = input("\nEnter the subject: ")
        topic = input("\nEnter the subject topic: ")
        description = input("\nEnter a description (optional): ")
        date = input("\nEnter the exam date (DD-MM-YYYY): ")
        if date == "":
            final_date = datetime.now(tz=None).strftime("%d-%m-%Y")
        else:
            final_date = date

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
        save_data(error_list)

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


def delete_database(data):
    with open(file_bank, "w", encoding="utf-8") as file:
        json.dump([], file)
        data.clear()
    print("\nDataBase deleted successfully!")


def main():
    errors = load_data()

    while True:
        print("\nError autopsy CLI")
        print("1. Log New Error")
        print("2. Exit")
        print("3. View error database")
        print("4. Delete database")

        option = input("Choose an option: ")

        if option == "1":
            register_error(errors)
        elif option == "2":
            print("Goodbye!")
            break
        elif option == "3":
            view_database(errors)
        elif option == "4":
            del_confirmation = input(
                '\nType "Confirm" to confirm you want to delete your previus DataBase: \n'
            )
            if del_confirmation == "Confirm":
                delete_database(errors)
            else:
                print("\nConfirmation incomplete. DataBase was NOT deleted")
        else:
            print("\nInvalid Option")


if __name__ == "__main__":
    main()
