# pysankey

Displays an interactive flow diagram representing team movement over time
Available as a standalone python app or a Hex app. Take your pick.

# Configure

## Standalone

.env

```
SPREADSHEET_ID=the google sheet key in the URL
SHEET_NAME=The name of the tab in the Google sheet (e.g. "Sheet1")
GOOGLE_CREDENTIALS=./your Google Sheets credential file for a service account.json
```

## Hex

Those same .env vars need to be stored as variables in Hex.
The credentials file needs to be uploaded into the projects "files" location.

# Install and run standalone

Not relevant for Hex

```bash
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
python3 pysankey.py
```
