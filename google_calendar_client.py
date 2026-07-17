import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/tasks.readonly",
]
TOKEN_FILE = Path("tokens/google_calendar_tasks_token.json")


class GoogleCalendarClient:
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
                    "Google Calendar token invalid or expired. Re-run: python setup_google_calendar_tasks.py"
                )

        self.service = build("calendar", "v3", credentials=creds)
        return self

    def get_upcoming_events(self, hours=24):
        now = datetime.now(timezone.utc)
        time_min = now.isoformat()
        time_max = (now + timedelta(hours=hours)).isoformat()

        response = self.service.events().list(
            calendarId="primary",
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime",
            maxResults=100,
        ).execute()

        return [self._parse_event(e) for e in response.get("items", [])]

    def _parse_event(self, event):
        start = event.get("start", {}).get("dateTime") or event.get("start", {}).get("date")
        end = event.get("end", {}).get("dateTime") or event.get("end", {}).get("date")
        attendees = [
            a.get("email") for a in event.get("attendees", []) if a.get("email")
        ]
        return {
            "id": event.get("id"),
            "title": event.get("summary", "(no title)"),
            "start": start,
            "end": end,
            "location": event.get("location", ""),
            "description": event.get("description", ""),
            "attendees": attendees,
        }
