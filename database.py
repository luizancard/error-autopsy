import json
import os

file_bank = "error_log.json"


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


def delete_database(data):
    with open(file_bank, "w", encoding="utf-8") as file:
        json.dump([], file)
        data.clear()
    print("\nDataBase deleted successfully!")
