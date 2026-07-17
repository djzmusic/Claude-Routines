from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/tasks.readonly",
]
TOKEN_FILE = Path("tokens/google_calendar_tasks_token.json")


class GoogleTasksClient:
    def __init__(self):
        self.service = None

    def authenticate(self):
        if not TOKEN_FILE.exists():
            raise FileNotFoundError(
                "Google Calendar/Tasks not authorized yet. Run: python setup_google_calendar_tasks.py"
            )

        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        if not creds.valid:
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                TOKEN_FILE.write_text(creds.to_json())
            else:
                raise RuntimeError(
                    "Google Tasks token invalid or expired. Re-run: python setup_google_calendar_tasks.py"
                )

        self.service = build("tasks", "v1", credentials=creds)
        return self

    def get_tasks(self):
        tasklists = self.service.tasklists().list().execute().get("items", [])

        results = []
        for tasklist in tasklists:
            tasks = self.service.tasks().list(
                tasklist=tasklist["id"],
                showCompleted=False,
                showHidden=False,
            ).execute().get("items", [])

            for task in tasks:
                results.append({
                    "id": task["id"],
                    "list": tasklist.get("title", ""),
                    "title": task.get("title", "(untitled task)"),
                    "notes": task.get("notes", ""),
                    "due": task.get("due"),
                    "status": task.get("status", "needsAction"),
                })

        return results
