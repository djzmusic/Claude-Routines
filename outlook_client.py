import os
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import msal
import requests

TOKEN_FILE = Path("tokens/outlook_token.json")
GRAPH_BASE = "https://graph.microsoft.com/v1.0"
SCOPES = ["Mail.ReadWrite", "User.Read"]


class OutlookClient:
    def __init__(self):
        self.token = None
        self.client_id = os.getenv("OUTLOOK_CLIENT_ID")
        self.client_secret = os.getenv("OUTLOOK_CLIENT_SECRET")
        self.tenant_id = os.getenv("OUTLOOK_TENANT_ID", "common")

    def authenticate(self):
        if not self.client_id:
            raise ValueError(
                "OUTLOOK_CLIENT_ID not set in .env. See README.md for setup instructions."
            )

        authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        app = msal.PublicClientApplication(self.client_id, authority=authority)

        # Try cached token first
        accounts = app.get_accounts()
        if accounts and TOKEN_FILE.exists():
            result = app.acquire_token_silent(SCOPES, account=accounts[0])
            if result and "access_token" in result:
                self.token = result["access_token"]
                return self

        # Device code flow — user opens a URL and enters a code (no redirect needed)
        flow = app.initiate_device_flow(scopes=SCOPES)
        if "user_code" not in flow:
            raise RuntimeError(f"Outlook auth failed: {flow.get('error_description')}")

        print(f"\n[Outlook] {flow['message']}\n")
        result = app.acquire_token_by_device_flow(flow)

        if "access_token" not in result:
            raise RuntimeError(f"Outlook auth failed: {result.get('error_description')}")

        self.token = result["access_token"]
        TOKEN_FILE.parent.mkdir(exist_ok=True)
        TOKEN_FILE.write_text(json.dumps(result))
        return self

    def _headers(self):
        return {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}

    def get_recent_messages(self, hours=24):
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        cutoff_str = cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")

        url = (
            f"{GRAPH_BASE}/me/messages"
            f"?$filter=receivedDateTime ge {cutoff_str}"
            f"&$select=id,from,subject,receivedDateTime,internetMessageHeaders,bodyPreview,body"
            f"&$top=100"
        )

        results = []
        while url:
            resp = requests.get(url, headers=self._headers())
            resp.raise_for_status()
            data = resp.json()
            for msg in data.get("value", []):
                results.append(self._parse_message(msg))
            url = data.get("@odata.nextLink")

        return results

    def _parse_message(self, msg):
        headers = {h["name"]: h["value"] for h in msg.get("internetMessageHeaders", [])}
        body_text = re.sub(r"<[^>]+>", " ", msg.get("body", {}).get("content", ""))
        return {
            "id": msg["id"],
            "source": "outlook",
            "from": msg.get("from", {}).get("emailAddress", {}).get("address", ""),
            "subject": msg.get("subject", "(no subject)"),
            "date": msg.get("receivedDateTime", ""),
            "list_unsubscribe": headers.get("List-Unsubscribe", ""),
            "precedence": headers.get("Precedence", ""),
            "body_preview": body_text[:1000],
        }

    def trash_message(self, msg_id):
        url = f"{GRAPH_BASE}/me/messages/{msg_id}/move"
        payload = {"destinationId": "deleteditems"}
        resp = requests.post(url, headers=self._headers(), json=payload)
        resp.raise_for_status()

    def set_priority_category(self, msg_id, priority, category):
        categories = [f"Priority: {priority}"]
        if category:
            categories.append(f"Business: {category}")

        importance_map = {"High": "high", "Medium": "normal", "Low": "low"}
        payload = {
            "importance": importance_map.get(priority, "normal"),
            "categories": categories,
        }
        url = f"{GRAPH_BASE}/me/messages/{msg_id}"
        resp = requests.patch(url, headers=self._headers(), json=payload)
        resp.raise_for_status()
