import os
import re
import json
import logging
from datetime import datetime, timedelta, timezone
from anthropic import Anthropic

from email_processor import UNSUBSCRIBE_PATTERNS

logger = logging.getLogger(__name__)

PREP_KEYWORDS = [
    "review", "prepare", "bring", "presentation", "demo", "pitch",
    "interview", "deck", "proposal", "agenda", "report",
]


class BriefingProcessor:
    """Assembles the daily morning briefing: schedule, unread email triage,
    Google Tasks, implied action items, and an automatic junk-email sweep."""

    def __init__(self, gmail_client=None, calendar_client=None, tasks_client=None, dry_run=False):
        self.gmail = gmail_client
        self.calendar = calendar_client
        self.tasks = tasks_client
        self.dry_run = dry_run or os.getenv("DRY_RUN", "false").lower() == "true"
        self.ai = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def run(self):
        briefing = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "schedule": [],
            "emails": {"urgent": [], "important": [], "fyi": []},
            # No chat/messaging platform (Slack, Teams, etc.) is wired up in this
            # codebase yet, so this always comes back empty until one is added.
            "messages_awaiting_reply": [],
            "tasks": {"overdue": [], "due_this_week": [], "upcoming": []},
            "action_items": [],
            "junk_cleanup": {"removed": [], "flagged": [], "dry_run": self.dry_run},
            "errors": [],
        }

        unread_emails = []

        if self.calendar:
            try:
                briefing["schedule"] = self._build_schedule()
            except Exception as e:
                briefing["errors"].append(f"Calendar fetch error: {e}")

        if self.gmail:
            try:
                unread_emails = self.gmail.get_unread_messages()
                briefing["emails"] = self._triage_emails(unread_emails)
            except Exception as e:
                briefing["errors"].append(f"Gmail fetch error: {e}")

            try:
                briefing["junk_cleanup"] = self._cleanup_junk()
            except Exception as e:
                briefing["errors"].append(f"Junk cleanup error: {e}")

        if self.tasks:
            try:
                briefing["tasks"] = self._build_tasks()
            except Exception as e:
                briefing["errors"].append(f"Tasks fetch error: {e}")

        try:
            briefing["action_items"] = self._extract_action_items(briefing["schedule"], unread_emails)
        except Exception as e:
            briefing["errors"].append(f"Action item extraction error: {e}")

        return briefing

    # ── Schedule ──────────────────────────────────────────────────────────

    def _build_schedule(self):
        events = self.calendar.get_upcoming_events(hours=24)
        schedule = []
        for event in events:
            schedule.append({
                "title": event["title"],
                "start": event["start"],
                "end": event["end"],
                "location": event.get("location", ""),
                "attendees": event.get("attendees", []),
                "prep_needed": self._flag_prep(event),
            })
        return schedule

    def _flag_prep(self, event):
        text = f"{event.get('title', '')} {event.get('description', '')}".lower()
        matches = [kw for kw in PREP_KEYWORDS if kw in text]
        return f"Prep likely needed ({', '.join(matches)})" if matches else None

    # ── Important emails ─────────────────────────────────────────────────

    def _triage_emails(self, emails):
        tiers = {"urgent": [], "important": [], "fyi": []}
        for email in emails:
            try:
                result = self._summarize_and_tier(email)
            except Exception as e:
                logger.warning(f"AI triage failed for '{email.get('subject')}': {e}")
                result = {"tier": "fyi", "summary": email.get("subject", "")}

            entry = {
                "subject": email.get("subject", ""),
                "from": email.get("from", ""),
                "summary": result.get("summary", ""),
            }
            tier = result.get("tier") if result.get("tier") in tiers else "fyi"
            tiers[tier].append(entry)
        return tiers

    def _summarize_and_tier(self, email):
        prompt = f"""Summarize this email in one short sentence and classify its urgency tier. Respond with ONLY a valid JSON object.

From: {email.get('from', 'Unknown')}
Subject: {email.get('subject', '(no subject)')}
Preview: {email.get('body_preview', '')[:600]}

Return this exact JSON structure (no other text):
{{
  "summary": <one short sentence summary>,
  "tier": <"urgent" if it needs action today, "important" if it needs action this week, "fyi" if no action is needed>
}}"""
        return self._ask_ai(prompt, default={"summary": email.get("subject", ""), "tier": "fyi"})

    # ── Google Tasks ──────────────────────────────────────────────────────

    def _build_tasks(self):
        now = datetime.now(timezone.utc)
        week_end = now + timedelta(days=7)
        groups = {"overdue": [], "due_this_week": [], "upcoming": []}

        for task in self.tasks.get_all_tasks():
            entry = {
                "title": task["title"],
                "list": task["list"],
                "due": task.get("due"),
                "notes": task.get("notes", ""),
            }
            due_str = task.get("due")
            if not due_str:
                groups["upcoming"].append(entry)
                continue

            due_dt = datetime.fromisoformat(due_str.replace("Z", "+00:00"))
            if due_dt < now:
                groups["overdue"].append(entry)
            elif due_dt <= week_end:
                groups["due_this_week"].append(entry)
            else:
                groups["upcoming"].append(entry)

        for key in groups:
            groups[key].sort(key=lambda t: t.get("due") or "9999")

        return groups

    # ── Action items ──────────────────────────────────────────────────────

    def _extract_action_items(self, schedule, unread_emails):
        if not schedule and not unread_emails:
            return []

        context_lines = [f"- Calendar: {e['title']} at {e['start']}" for e in schedule[:10]]
        context_lines += [
            f"- Email from {e.get('from')}: {e.get('subject')} — {e.get('body_preview', '')[:200]}"
            for e in unread_emails[:15]
        ]

        prompt = f"""Given today's calendar events and unread emails below, identify any implied follow-ups or action items that haven't been formally logged as tasks. Only include genuinely actionable items — skip anything already an obvious task. Respond with ONLY a valid JSON object.

{chr(10).join(context_lines)}

Return this exact JSON structure (no other text):
{{"action_items": [<short imperative strings, e.g. "Reply to Jane re: contract terms">]}}"""
        result = self._ask_ai(prompt, default={"action_items": []}, max_tokens=400)
        return result.get("action_items", [])

    # ── Junk cleanup ──────────────────────────────────────────────────────

    def _cleanup_junk(self):
        emails = self.gmail.get_recent_messages(hours=24)
        removed, flagged = [], []

        for email in emails:
            if self._is_junk_by_headers(email):
                self._trash(email)
                removed.append({
                    "subject": email.get("subject", ""),
                    "from": email.get("from", ""),
                    "reason": "Unsubscribe link / bulk mail header detected",
                })
                continue

            verdict = self._classify_junk_with_ai(email)
            if not verdict.get("is_junk"):
                continue

            entry = {
                "subject": email.get("subject", ""),
                "from": email.get("from", ""),
                "reason": verdict.get("reason", "Looks promotional"),
            }
            if verdict.get("confidence") == "high":
                self._trash(email)
                removed.append(entry)
            else:
                flagged.append(entry)

        return {"removed": removed, "flagged": flagged, "dry_run": self.dry_run}

    def _is_junk_by_headers(self, email):
        if email.get("list_unsubscribe"):
            return True
        if email.get("precedence", "").lower() in ("bulk", "list", "junk"):
            return True
        if UNSUBSCRIBE_PATTERNS.search(email.get("body_preview", "")):
            return True
        return False

    def _classify_junk_with_ai(self, email):
        prompt = f"""Classify whether this email is junk (spam, promotional, or marketing). Respond with ONLY a valid JSON object.

From: {email.get('from', 'Unknown')}
Subject: {email.get('subject', '(no subject)')}
Preview: {email.get('body_preview', '')[:600]}

Return this exact JSON structure (no other text):
{{
  "is_junk": <true or false>,
  "confidence": <"high" if clearly junk, "borderline" if uncertain, null if not junk>,
  "reason": <one short sentence explaining your decision>
}}"""
        return self._ask_ai(prompt, default={"is_junk": False})

    def _trash(self, email):
        if self.dry_run:
            logger.info(f"[DRY RUN] Would trash: {email.get('subject')}")
            return
        self.gmail.trash_message(email["id"])

    # ── AI helper ─────────────────────────────────────────────────────────

    def _ask_ai(self, prompt, default, max_tokens=200):
        response = self.ai.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return default
