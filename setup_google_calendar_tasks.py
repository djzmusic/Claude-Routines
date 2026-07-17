"""
Run this once to authorize Google Calendar + Tasks access and save your token.
Usage:  python setup_google_calendar_tasks.py
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

load_dotenv()
SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/tasks.readonly",
]
TOKEN_FILE = Path("tokens/google_calendar_tasks_token.json")


def main():
    creds_file = os.getenv(
        "GOOGLE_CREDENTIALS_FILE", os.getenv("GMAIL_CREDENTIALS_FILE", "credentials_gmail.json")
    )
    if not Path(creds_file).exists():
        print(f"\nERROR: '{creds_file}' not found.")
        print("Follow these steps:")
        print("  1. Go to https://console.cloud.google.com/ (reuse your Gmail project, or create a new one)")
        print("  2. Enable the Google Calendar API and Google Tasks API: APIs & Services → Library")
        print("  3. Create an OAuth client ID (Desktop app) — or reuse your existing Gmail one")
        print("  4. Download the JSON file and save it as:", creds_file)
        print("  5. Run this script again.\n")
        return

    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if creds and creds.valid:
        print("Google Calendar/Tasks are already authorized!")
        return
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
        creds = flow.run_local_server(port=0)

    TOKEN_FILE.parent.mkdir(exist_ok=True)
    TOKEN_FILE.write_text(creds.to_json())
    print("\nGoogle Calendar/Tasks authorized successfully! Token saved to", TOKEN_FILE)


if __name__ == "__main__":
    main()
