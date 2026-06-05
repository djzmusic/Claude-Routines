import os
import re
import json
import logging
from anthropic import Anthropic

logger = logging.getLogger(__name__)

UNSUBSCRIBE_PATTERNS = re.compile(
    r"(unsubscribe|opt.?out|manage.{0,20}preference|email.{0,20}preference|"
    r"remove.{0,10}list|no longer.{0,10}receive|stop receiving)",
    re.IGNORECASE,
)

PRIORITY_LABELS = {
    "High": ["Priority/High"],
    "Medium": ["Priority/Medium"],
    "Low": ["Priority/Low"],
}

CATEGORY_LABEL_PREFIX = "Category"


class EmailProcessor:
    def __init__(self, gmail_client=None, outlook_client=None, dry_run=False):
        self.gmail = gmail_client
        self.outlook = outlook_client
        self.dry_run = dry_run or os.getenv("DRY_RUN", "false").lower() == "true"
        self.ai = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.hours = int(os.getenv("LOOKBACK_HOURS", "24"))

    def run(self):
        summary = {
            "trashed": [],
            "prioritized": [],
            "errors": [],
            "dry_run": self.dry_run,
        }

        emails = []
        if self.gmail:
            try:
                gmail_emails = self.gmail.get_recent_messages(hours=self.hours)
                emails.extend(gmail_emails)
                logger.info(f"Fetched {len(gmail_emails)} emails from Gmail")
            except Exception as e:
                summary["errors"].append(f"Gmail fetch error: {e}")

        if self.outlook:
            try:
                outlook_emails = self.outlook.get_recent_messages(hours=self.hours)
                emails.extend(outlook_emails)
                logger.info(f"Fetched {len(outlook_emails)} emails from Outlook")
            except Exception as e:
                summary["errors"].append(f"Outlook fetch error: {e}")

        for email in emails:
            try:
                self._process_email(email, summary)
            except Exception as e:
                summary["errors"].append(f"Error processing '{email.get('subject')}': {e}")

        return summary

    def _process_email(self, email, summary):
        subject = email.get("subject", "")
        sender = email.get("from", "")
        source = email.get("source", "")

        if self._is_junk_by_headers(email):
            reason = "Unsubscribe link / bulk mail header detected"
            self._trash(email)
            summary["trashed"].append({
                "subject": subject,
                "from": sender,
                "source": source,
                "reason": reason,
            })
            return

        classification = self._classify_with_ai(email)

        if classification.get("is_junk"):
            self._trash(email)
            summary["trashed"].append({
                "subject": subject,
                "from": sender,
                "source": source,
                "reason": classification.get("reason", "AI: junk/promotional"),
            })
        else:
            priority = classification.get("priority", "Low")
            category = classification.get("category", "Other")
            self._apply_priority(email, priority, category)
            summary["prioritized"].append({
                "subject": subject,
                "from": sender,
                "source": source,
                "priority": priority,
                "category": category,
                "reason": classification.get("reason", ""),
            })

    def _is_junk_by_headers(self, email):
        # List-Unsubscribe header is definitive proof of bulk/marketing mail
        if email.get("list_unsubscribe"):
            return True
        # Precedence: bulk or list signals automated email
        precedence = email.get("precedence", "").lower()
        if precedence in ("bulk", "list", "junk"):
            return True
        # Check body for unsubscribe links
        if UNSUBSCRIBE_PATTERNS.search(email.get("body_preview", "")):
            return True
        return False

    def _classify_with_ai(self, email):
        prompt = f"""You are an email triage assistant. Classify this email and respond with ONLY a valid JSON object.

From: {email.get('from', 'Unknown')}
Subject: {email.get('subject', '(no subject)')}
Preview: {email.get('body_preview', '')[:600]}

Return this exact JSON structure (no other text):
{{
  "is_junk": <true if promotional/newsletter/marketing/automated, false if genuine business communication>,
  "priority": <"High" if urgent/time-sensitive/financial/legal/client request, "Medium" if needs a reply, "Low" if FYI/informational, null if is_junk>,
  "category": <"Finance" | "Legal" | "Client" | "Vendor" | "Operations" | "HR" | "Sales" | "Other" | null if is_junk>,
  "reason": <one short sentence explaining your decision>
}}"""

        response = self.ai.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        # Extract JSON even if there's surrounding whitespace
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return {"is_junk": False, "priority": "Low", "category": "Other", "reason": "Could not parse AI response"}

    def _trash(self, email):
        if self.dry_run:
            logger.info(f"[DRY RUN] Would trash: {email['subject']}")
            return
        if email["source"] == "gmail" and self.gmail:
            self.gmail.trash_message(email["id"])
        elif email["source"] == "outlook" and self.outlook:
            self.outlook.trash_message(email["id"])

    def _apply_priority(self, email, priority, category):
        if self.dry_run:
            logger.info(f"[DRY RUN] Would label '{email['subject']}' as {priority}/{category}")
            return
        if email["source"] == "gmail" and self.gmail:
            labels = PRIORITY_LABELS.get(priority, ["Priority/Low"])
            if category and category != "Other":
                labels.append(f"{CATEGORY_LABEL_PREFIX}/{category}")
            self.gmail.apply_labels(email["id"], labels)
        elif email["source"] == "outlook" and self.outlook:
            self.outlook.set_priority_category(email["id"], priority, category)
