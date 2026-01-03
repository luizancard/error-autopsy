import json
import os
from datetime import date, datetime
from pathlib import Path

# Build absolute path to data/error_log.json
# File is in src/services/db_service.py -> Go up 3 levels to project root
BASE_DIR = Path(__file__).resolve().parent.parent.parent
file_bank = BASE_DIR / "data" / "error_log.json"


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


def log_error(data, subject, topic, error_type, description, date_val):
    """
    Logs a new error to the data list and saves it.
    Attributes:
        data (list): The list of error records.
        subject (str): The subject of the error.
        topic (str): The topic of the error.
        error_type (str): The type of error.
        description (str): Description or reflection.
        date_val (str or datetime.date): The date of the error.
    """

    # Ensure date is formatted as DD-MM-YYYY
    if isinstance(date_val, (date, datetime)):
        date_str = date_val.strftime("%d-%m-%Y")
    else:
        # If it's a string, try to parse and reformat, or assume standard ISO
        # But safest is to trust it if it matches, or force reformat if it's ISO YYYY-MM-DD
        try:
            # Try parsing ISO
            parsed = datetime.strptime(str(date_val), "%Y-%m-%d")
            date_str = parsed.strftime("%d-%m-%Y")
        except ValueError:
            # Assume it's already in correct format or raw string
            date_str = str(date_val)

    new_entry = {
        "subject": subject,
        "topic": topic,
        "type": error_type,
        "description": description,
        "date": date_str,
    }

    data.append(new_entry)
    save_data(data)
