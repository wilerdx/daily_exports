#!/usr/bin/env python3

import os
import datetime
import pandas as pd
import tomllib
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# === Config ===

SCOPES = [
  'https://www.googleapis.com/auth/spreadsheets.readonly',
  'https://www.googleapis.com/auth/drive.file',
  'https://www.googleapis.com/auth/drive.metadata.readonly'
]

def load_config(path='config.toml'):
    script_dir = os.path.dirname(os.path.realpath(__file__))
    config_path = os.path.join(script_dir, path)
    with open(config_path, 'rb') as f:
        return tomllib.load(f)

def validate_config(config):
    required = {
        'gdrive': ['credentials', 'token'],
        'sheets': ['spreadsheet_id', 'sheets'],
        'drive': ['main_folder_id']
    }

    for section, keys in required.items():
        if section not in config:
            raise ValueError(f"Missing section: [{section}] in config.toml")
        for key in keys:
            if key not in config[section]:
                raise ValueError(f"Missing key: '{key}' under [{section}] in config.toml")
            
config = load_config()
validate_config(config)

CREDENTIALS = os.path.expanduser(config['gdrive']['credentials'])
TOKEN = os.path.expanduser(config['gdrive']['token'])
SPREADSHEET_ID = config['sheets']['spreadsheet_id']
SHEETS = config['sheets']['sheets']
MAIN_FOLDER_ID = config['drive']['main_folder_id'] 

# === Authentication ===
def get_credentials():
    creds = None
    if os.path.exists(TOKEN):
        creds = Credentials.from_authorized_user_file(TOKEN, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS, SCOPES)
            creds = flow.run_local_server(port=0)
            with open(TOKEN, 'w') as token:
                token.write(creds.to_json())
    return creds

# === Find or create month folder in Drive ===
def find_or_create_month_folder(service_drive, parent_folder_id, month_year_name):
    query = (
        f"mimeType='application/vnd.google-apps.folder' and "
        f"'{parent_folder_id}' in parents and "
        f"name = '{month_year_name}' and trashed = false"
    )
    results = service_drive.files().list(q=query, fields="files(id, name)").execute()
    folders = results.get('files', [])
    if folders:
        print("--------------------------------------------------")
        print(f"📂 Found existing folder: '{month_year_name}'")
        return folders[0]['id']

    folder_metadata = {
        'name': month_year_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_folder_id]
    }
    folder = service_drive.files().create(body=folder_metadata, fields='id').execute()
    print(f"🆕 Created folder: '{month_year_name}' (ID: {folder['id']})")
    return folder['id']

# === Upload a file to Google Drive folder ===
def upload_to_drive(service_drive, file_path, folder_id):
    filename = os.path.basename(file_path)

    # Check if file with same name exists in folder
    query = f"name = '{filename}' and '{folder_id}' in parents and trashed = false"
    response = service_drive.files().list(q=query, fields="files(id, name)").execute()
    files = response.get('files', [])

    media = MediaFileUpload(file_path, mimetype='text/csv')

    if files:
        # Update existing file
        file_id = files[0]['id']
        service_drive.files().update(
            fileId=file_id,
            media_body=media
        ).execute()
        print(f"♻️ Updated existing file on Drive: {filename}")
    else:
        # Create new file
        file_metadata = {
            'name': filename,
            'parents': [folder_id]
        }
        service_drive.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        print(f"✅ Uploaded new file to Drive: {filename}")

# === Download sheet, save locally, then upload ===
def download_sheet(service_sheets, service_drive, sheet_name, month_folder_id):
    try:
        result = service_sheets.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=sheet_name
        ).execute()
    except Exception as e:
        print(f'❌ Error downloading sheet "{sheet_name}": {e}')
        return

    values = result.get('values', [])
    if not values:
        print(f'⚠️ No data in sheet "{sheet_name}".')
        return

    header = values[0]
    data = values[1:]

    # Pad header if data rows have more columns than header
    max_cols = max(len(row) for row in data) if data else len(header)
    if max_cols > len(header):
        extra_cols = max_cols - len(header)
        header += [f"Extra_Column_{i+1}" for i in range(extra_cols)]

    df = pd.DataFrame(data)
    df.columns = header

    today_str = datetime.datetime.now().strftime('%m%d%y')
    filename_map = {
        'Data_Set': f'Pricing Booster - Data_Set {today_str}.csv',
        'Output': f'Pricing Booster - Output {today_str}.csv'
    }
    local_filename = filename_map.get(sheet_name, f'{sheet_name} {today_str}.csv')
    local_path = os.path.join(os.path.expanduser('~/Downloads'), local_filename)

    df.to_csv(local_path, index=False)
    print(f"📁 Saved: {local_path}")

    upload_to_drive(service_drive, local_path, month_folder_id)

# === Main ===
if __name__ == '__main__':
    try:
        creds = get_credentials()
        service_sheets = build('sheets', 'v4', credentials=creds)
        service_drive = build('drive', 'v3', credentials=creds)

        month_folder_name = datetime.datetime.now().strftime('%B %Y')  # e.g. "July 2025"
        month_folder_id = find_or_create_month_folder(service_drive, MAIN_FOLDER_ID, month_folder_name)

        for sheet in SHEETS:
            download_sheet(service_sheets, service_drive, sheet, month_folder_id)
    except Exception as e:
        import traceback
        print("❌ Script failed:", e)
        traceback.print_exc()