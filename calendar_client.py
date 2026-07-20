import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
TOKEN_FILE = Path("tokens/calendar_token.json")


class CalendarClient:
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

        self.service = build("calendar", "v3", credentials=creds)
        return self

    def get_upcoming_events(self, hours=24, max_results=25):
        now = datetime.now(timezone.utc)
        time_min = now.isoformat()
        time_max = (now + timedelta(hours=hours)).isoformat()

        response = self.service.events().list(
            calendarId="primary",
            timeMin=time_min,
            timeMax=time_max,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        ).execute()

        return [self._parse_event(e) for e in response.get("items", [])]

    def _parse_event(self, event):
        start = event.get("start", {})
        end = event.get("end", {})
        attendees = [
            a.get("email", "") for a in event.get("attendees", []) if a.get("email")
        ]
        return {
            "id": event.get("id", ""),
            "title": event.get("summary", "(no title)"),
            "description": event.get("description", ""),
            "location": event.get("location", ""),
            "start": start.get("dateTime", start.get("date", "")),
            "end": end.get("dateTime", end.get("date", "")),
            "all_day": "date" in start,
            "attendees": attendees,
        }
