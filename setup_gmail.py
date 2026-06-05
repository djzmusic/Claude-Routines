"""
Run this once to authorize Gmail access and save your token.
Usage:  python setup_gmail.py
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

load_dotenv()
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
TOKEN_FILE = Path("tokens/gmail_token.json")


def main():
    creds_file = os.getenv("GMAIL_CREDENTIALS_FILE", "credentials_gmail.json")
    if not Path(creds_file).exists():
        print(f"\nERROR: '{creds_file}' not found.")
        print("Follow these steps:")
        print("  1. Go to https://console.cloud.google.com/")
        print("  2. Create a project (or select an existing one)")
        print("  3. Enable the Gmail API: APIs & Services → Library → Gmail API → Enable")
        print("  4. Create credentials: APIs & Services → Credentials → + Create Credentials → OAuth client ID")
        print("  5. Application type: Desktop app")
        print("  6. Download the JSON file and save it as:", creds_file)
        print("  7. Run this script again.\n")
        return

    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if creds and creds.valid:
        print("Gmail is already authorized!")
        return
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
        creds = flow.run_local_server(port=0)

    TOKEN_FILE.parent.mkdir(exist_ok=True)
    TOKEN_FILE.write_text(creds.to_json())
    print("\nGmail authorized successfully! Token saved to", TOKEN_FILE)


if __name__ == "__main__":
    main()
