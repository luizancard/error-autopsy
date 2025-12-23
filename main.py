import json
import os
from datetime import datetime

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
    print("Saved succesfully!")


def register_error(error_list):
    try:
        subject = input("Enter the subject: ")
        topic = input("Enter the subject topic: ")
        description = input("Enter a description (optional): ")
        date = input("Enter the exam date (DD-MM-YYYY): ")
        if date == "":
            final_date = datetime.now(tz=None).strftime("%d-%m-%Y")
        else:
            final_date = date

        print("\nSelect the error type:")

        for code, name in error_types.items():
            print(f"[{code}]: {name}")

        while True:
            choice = input("Option number: ")
            if choice in error_types:
                error_name = error_types[choice]
                break
            else:
                print("Invalid option. Try again.")
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
        print("Invalid Input")


def main():
    errors = load_data()

    while True:
        print("Error autopsy CLI")
        print("1. Log New Error")
        print("2. Exit")
        option = input("Choose an option: ")

        if option == "1":
            register_error(errors)
        elif option == "2":
            print("Goodbye!")
            break
        else:
            print("Invalid Option")


if __name__ == "__main__":
    main()
