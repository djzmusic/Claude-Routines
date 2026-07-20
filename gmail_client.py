import os
import json
import base64
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
TOKEN_FILE = Path("tokens/gmail_token.json")


class GmailClient:
    def __init__(self):
        self.service = None
        self._label_cache = {}

    def authenticate(self):
        creds = None
        if TOKEN_FILE.exists():
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                creds_file = os.getenv("GMAIL_CREDENTIALS_FILE", "credentials_gmail.json")
                if not Path(creds_file).exists():
                    raise FileNotFoundError(
                        f"Gmail credentials file '{creds_file}' not found. "
                        "See README.md for setup instructions."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
                creds = flow.run_local_server(port=0)

            TOKEN_FILE.parent.mkdir(exist_ok=True)
            TOKEN_FILE.write_text(creds.to_json())

        self.service = build("gmail", "v1", credentials=creds)
        return self

    def get_recent_messages(self, hours=24):
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        after_ts = int(cutoff.timestamp())
        query = f"after:{after_ts} -in:trash -in:spam"

        results = []
        page_token = None

        while True:
            kwargs = {"userId": "me", "q": query, "maxResults": 100}
            if page_token:
                kwargs["pageToken"] = page_token
            response = self.service.users().messages().list(**kwargs).execute()

            msg_ids = [m["id"] for m in response.get("messages", [])]
            for msg_id in msg_ids:
                msg = self.service.users().messages().get(
                    userId="me", id=msg_id, format="full"
                ).execute()
                results.append(self._parse_message(msg))

            page_token = response.get("nextPageToken")
            if not page_token:
                break

        return results

    def get_unread_messages(self, max_results=50):
        query = "is:unread -in:trash -in:spam"

        results = []
        page_token = None

        while True:
            kwargs = {"userId": "me", "q": query, "maxResults": min(max_results, 100)}
            if page_token:
                kwargs["pageToken"] = page_token
            response = self.service.users().messages().list(**kwargs).execute()

            msg_ids = [m["id"] for m in response.get("messages", [])]
            for msg_id in msg_ids:
                msg = self.service.users().messages().get(
                    userId="me", id=msg_id, format="full"
                ).execute()
                results.append(self._parse_message(msg))
                if len(results) >= max_results:
                    return results

            page_token = response.get("nextPageToken")
            if not page_token:
                break

        return results

    def _parse_message(self, msg):
        headers = {h["name"]: h["value"] for h in msg["payload"].get("headers", [])}
        body = self._extract_body(msg["payload"])
        return {
            "id": msg["id"],
            "source": "gmail",
            "from": headers.get("From", ""),
            "subject": headers.get("Subject", "(no subject)"),
            "date": headers.get("Date", ""),
            "list_unsubscribe": headers.get("List-Unsubscribe", ""),
            "precedence": headers.get("Precedence", ""),
            "body_preview": body[:1000],
        }

    def _extract_body(self, payload):
        if payload.get("body", {}).get("data"):
            return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")
        for part in payload.get("parts", []):
            if part.get("mimeType") in ("text/plain", "text/html"):
                data = part.get("body", {}).get("data", "")
                if data:
                    text = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
                    # Strip HTML tags for plain text preview
                    text = re.sub(r"<[^>]+>", " ", text)
                    return text
        return ""

    def trash_message(self, msg_id):
        self.service.users().messages().trash(userId="me", id=msg_id).execute()

    def ensure_label(self, name):
        if name in self._label_cache:
            return self._label_cache[name]

        labels = self.service.users().labels().list(userId="me").execute().get("labels", [])
        for label in labels:
            if label["name"] == name:
                self._label_cache[name] = label["id"]
                return label["id"]

        created = self.service.users().labels().create(
            userId="me", body={"name": name}
        ).execute()
        self._label_cache[name] = created["id"]
        return created["id"]

    def apply_labels(self, msg_id, label_names):
        label_ids = [self.ensure_label(n) for n in label_names]
        self.service.users().messages().modify(
            userId="me",
            id=msg_id,
            body={"addLabelIds": label_ids},
        ).execute()
