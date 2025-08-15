# Daily Exports Scripts

Two Python scripts for automating Daily Exports downloads and data upload.

- **`daily_exports.py`** - Downloads sheets from Google Sheets, saves locally, and uploads to Google Drive
- **`exports_download.py`** - Downloads multiple sheets to local directories in order to be manually uploaded to marketplaces

## Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Set up Google Cloud Project with Sheets and Drive APIs enabled
3. Create OAuth 2.0 credentials and save as `/path/to/credentials.json`
4. Create `config.toml` in the same directory as the scripts

## Configuration

```toml
# config.toml

[gdrive] # gdrive is used for both scripts
credentials = "/path/to/credentials.json"
token = "/path/to/token.json" # Keep in the same direcotry as credentials

[sheets] # sheets is only for daily_exports.py
spreadsheet_id = "your-spreadsheet-id"
sheets = ["Sheet1", "Sheet2"]

[drive] # drive is only for daily_exports.py
main_folder_id = "your-drive-folder-id"

[export] # export is only for exports_download.py
export_spreadsheet_id = ["your-export-spreadsheet-id"]
export_sheets = [
    # Insert tab names from Daily Exports sheets. There will be more than 3
    "Sheet1",
    "Sheet2",
    "Sheet3"
    ] 
download_paths = [
    # Insert directory paths for the sheets to be saved to (same number and order as export_sheets)
    # Should be the respective directory for each marketplace in Dropbox
    "/path/to/dir1",
    "/path/to/dir2",
    "/path/to/dir3"
    ]
filenames = [
    # Insert filenames you want the sheets to be saved as (same number and order as export_sheets)
    # See Dropbox for recommended naming scheme
    # Use "{date}" for the today's date
    "File1_{date}.csv",
    "File2_{date}.csv",
    "File3_{date}.txt"
    ]
```

## Usage

```bash
python daily_exports.py    # Downloads and uploads to Drive
python exports_download.py # Downloads to local directories to be uploaded to marketplaces
```

## Notes

- `{date}` in filenames is replaced with current date (MMDDYY format)
- All arrays in `[export]` section must have the same length
- Download paths must exist and be writable
- Keep credentials secure and never commit to version control
