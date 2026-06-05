"""
Run this once to authorize Outlook/Office 365 access and save your token.
Usage:  python setup_outlook.py
"""
import os
import json
from pathlib import Path
from dotenv import load_dotenv
import msal

load_dotenv()
TOKEN_FILE = Path("tokens/outlook_token.json")
SCOPES = ["Mail.ReadWrite", "User.Read"]


def main():
    client_id = os.getenv("OUTLOOK_CLIENT_ID")
    tenant_id = os.getenv("OUTLOOK_TENANT_ID", "common")

    if not client_id:
        print("\nERROR: OUTLOOK_CLIENT_ID not set in .env")
        print("\nFollow these steps to register an Azure app:")
        print("  1. Go to https://portal.azure.com/")
        print("  2. Search for 'App registrations' → + New registration")
        print("  3. Name: Email Cleanup  |  Account type: Personal + work/school accounts")
        print("  4. After creating, copy the 'Application (client) ID' → set as OUTLOOK_CLIENT_ID in .env")
        print("  5. Copy the 'Directory (tenant) ID' → set as OUTLOOK_TENANT_ID in .env")
        print("  6. Go to API permissions → Add → Microsoft Graph → Delegated:")
        print("     Mail.ReadWrite, User.Read → Grant admin consent")
        print("  7. Run this script again.\n")
        return

    authority = f"https://login.microsoftonline.com/{tenant_id}"
    app = msal.PublicClientApplication(client_id, authority=authority)

    flow = app.initiate_device_flow(scopes=SCOPES)
    if "user_code" not in flow:
        print("Failed to start device flow:", flow.get("error_description"))
        return

    print("\n" + flow["message"])
    result = app.acquire_token_by_device_flow(flow)

    if "access_token" not in result:
        print("Authorization failed:", result.get("error_description"))
        return

    TOKEN_FILE.parent.mkdir(exist_ok=True)
    TOKEN_FILE.write_text(json.dumps(result))
    print("\nOutlook authorized successfully! Token saved to", TOKEN_FILE)


if __name__ == "__main__":
    main()
