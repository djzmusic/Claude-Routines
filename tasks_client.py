import os
from pathlib import Path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/tasks.readonly"]
TOKEN_FILE = Path("tokens/tasks_token.json")


class TasksClient:
    def __init__(self):
        self.service = None

    def authenticate(self):
        creds = None
        if TOKEN_FILE.exists():
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                creds_file = os.getenv(
                    "GOOGLE_CREDENTIALS_FILE",
                    os.getenv("GMAIL_CREDENTIALS_FILE", "credentials_gmail.json"),
                )
                if not Path(creds_file).exists():
                    raise FileNotFoundError(
                        f"Google credentials file '{creds_file}' not found. "
                        "See README.md for setup instructions."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
                creds = flow.run_local_server(port=0)

            TOKEN_FILE.parent.mkdir(exist_ok=True)
            TOKEN_FILE.write_text(creds.to_json())

        self.service = build("tasks", "v1", credentials=creds)
        return self

    def get_all_tasks(self):
        results = []
        lists_response = self.service.tasklists().list(maxResults=100).execute()

        for tasklist in lists_response.get("items", []):
            page_token = None
            while True:
                kwargs = {
                    "tasklist": tasklist["id"],
                    "showCompleted": False,
                    "maxResults": 100,
                }
                if page_token:
                    kwargs["pageToken"] = page_token
                response = self.service.tasks().list(**kwargs).execute()

                for task in response.get("items", []):
                    if task.get("status") == "completed":
                        continue
                    results.append({
                        "id": task.get("id", ""),
                        "title": task.get("title", "(untitled)"),
                        "notes": task.get("notes", ""),
                        "due": task.get("due"),
                        "list": tasklist.get("title", ""),
                    })

                page_token = response.get("nextPageToken")
                if not page_token:
                    break

        return results
