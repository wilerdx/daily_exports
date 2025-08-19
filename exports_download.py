import os
import csv
import datetime
import tomli as toml
from pathlib import Path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Load configuration
with open("config.toml", "rb") as f:
    config = toml.load(f)

# Expand paths with tilde
CREDENTIALS_PATH = Path(config["gdrive"]["credentials"]).expanduser()
TOKEN_PATH = Path(config["gdrive"]["token"]).expanduser()

# Get configuration values
SPREADSHEET_ID = config["export"]["export_spreadsheet_id"][0]
SHEET_NAMES = config["export"]["export_sheets"]
DOWNLOAD_PATHS = config["export"]["download_paths"]
FILENAME_TEMPLATES = config["export"]["filenames"]

# Date format for filenames
today_str = datetime.datetime.now().strftime("%m%d%y")

# Generate actual filenames with today's date
FILENAMES = [template.replace("{date}", today_str) for template in FILENAME_TEMPLATES]

# Authenticate with Google Sheets API
creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), ["https://www.googleapis.com/auth/spreadsheets.readonly"])
service = build('sheets', 'v4', credentials=creds)

for i, sheet_name in enumerate(SHEET_NAMES):
    filename = FILENAMES[i]
    ext = filename.split('.')[-1].lower()  # Extract extension from filename
    save_dir = DOWNLOAD_PATHS[i]

    print(f"Downloading: {sheet_name} → {filename}")

    try:
        # Request the full range from the sheet
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=sheet_name
        ).execute()
    except Exception as e:
        print(f"  Error: Could not access sheet '{sheet_name}': {str(e)}")
        print("Trying with quotes around sheet name...")
        try:
            # Try with quotes in case of special characters
            result = service.spreadsheets().values().get(
                spreadsheetId=SPREADSHEET_ID,
                range=f"'{sheet_name}'"
            ).execute()
            print("Success with quoted sheet name!")
        except Exception as e2:
            print(f"  Still failed with quotes: {str(e2)}")
            print("Skipping this sheet...")
            continue

    values = result.get('values', [])

    if not values:
        print(f"  Warning: No data found in '{sheet_name}'")
        continue

    # Remove empty row at the end if it exists
    if values and all(not cell or str(cell).strip() == '' for cell in values[-1]):
        values.pop()

    # No special processing needed - all sheets processed the same way

    # Make sure directory exists
    os.makedirs(save_dir, exist_ok=True)
    file_path = os.path.join(save_dir, filename)

    # Save file
    if ext == "csv":
        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
            writer.writerows(values)
        # Remove trailing newline if it exists
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        if content.endswith('\n'):
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content.rstrip('\n'))
    elif ext == "txt":
        with open(file_path, "w", encoding="utf-8") as f:
            for row in values:
                f.write("\t".join(map(str, row)) + "\n")
        # Remove trailing newline if it exists
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        if content.endswith('\n'):
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content.rstrip('\n'))

    print(f"  Saved to {file_path}")

print("All files downloaded successfully.")
