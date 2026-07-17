import os
import re
import json
import logging
from datetime import datetime, timedelta, timezone
from anthropic import Anthropic

logger = logging.getLogger(__name__)

PREP_KEYWORDS = re.compile(
    r"(prepare|prep\b|review|bring|presentation|deck|demo|pitch|interview|"
    r"agenda|slides|report due|deliverable|proposal)",
    re.IGNORECASE,
)

MODEL = "claude-haiku-4-5-20251001"


class MorningBriefing:
    def __init__(self, gmail_client=None, calendar_client=None, tasks_client=None, dry_run=False):
        self.gmail = gmail_client
        self.calendar = calendar_client
        self.tasks = tasks_client
        self.dry_run = dry_run or os.getenv("DRY_RUN", "false").lower() == "true"
        self.ai = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.lookahead_hours = int(os.getenv("BRIEFING_LOOKAHEAD_HOURS", "24"))
        self.lookback_hours = int(os.getenv("LOOKBACK_HOURS", "24"))

    def generate(self):
        briefing = {
            "date": datetime.now().astimezone().strftime("%A, %B %-d, %Y"),
            "schedule": [],
            "emails": {"urgent": [], "important": [], "fyi": []},
            "tasks": {"overdue": [], "due_soon": [], "upcoming": []},
            "action_items": [],
            "junk_cleanup": {"trashed": [], "flagged": [], "dry_run": self.dry_run},
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

        if self.tasks:
            try:
                briefing["tasks"] = self._build_tasks()
            except Exception as e:
                briefing["errors"].append(f"Tasks fetch error: {e}")

        try:
            briefing["action_items"] = self._surface_action_items(briefing["schedule"], unread_emails)
        except Exception as e:
            briefing["errors"].append(f"Action item extraction error: {e}")

        if self.gmail:
            try:
                briefing["junk_cleanup"] = self._cleanup_junk()
            except Exception as e:
                briefing["errors"].append(f"Junk cleanup error: {e}")

        return briefing

    # ── Schedule ──────────────────────────────────────────────────────────

    def _build_schedule(self):
        events = self.calendar.get_upcoming_events(hours=self.lookahead_hours)
        schedule = []
        for e in events:
            schedule.append({
                "title": e["title"],
                "start": e["start"],
                "end": e["end"],
                "location": e["location"],
                "attendees": e["attendees"],
                "prep_needed": self._needs_prep(e),
            })
        schedule.sort(key=lambda x: x["start"] or "")
        return schedule

    def _needs_prep(self, event):
        text = f"{event.get('title', '')} {event.get('description', '')}"
        return bool(PREP_KEYWORDS.search(text))

    # ── Emails ────────────────────────────────────────────────────────────

    def _triage_emails(self, emails):
        tiers = {"urgent": [], "important": [], "fyi": []}
        for email in emails:
            try:
                result = self._classify_urgency(email)
            except Exception as e:
                logger.warning(f"Could not classify '{email.get('subject')}': {e}")
                result = {"tier": "fyi", "summary": email.get("subject", "")}

            tier = result.get("tier", "fyi")
            if tier not in tiers:
                tier = "fyi"
            tiers[tier].append({
                "subject": email.get("subject", "(no subject)"),
                "from": email.get("from", ""),
                "summary": result.get("summary", ""),
            })
        return tiers

    def _classify_urgency(self, email):
        prompt = f"""Classify this unread email's urgency and summarize it in one sentence. Respond with ONLY valid JSON.

From: {email.get('from', 'Unknown')}
Subject: {email.get('subject', '(no subject)')}
Preview: {email.get('body_preview', '')[:600]}

Return this exact JSON structure (no other text):
{{
  "tier": <"urgent" if it needs action today, "important" if it needs action this week, "fyi" if no action needed>,
  "summary": <one short sentence summarizing the email>
}}"""
        response = self.ai.messages.create(
            model=MODEL,
            max_tokens=150,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return {"tier": "fyi", "summary": email.get("subject", "")}

    # ── Tasks ─────────────────────────────────────────────────────────────

    def _build_tasks(self):
        all_tasks = self.tasks.get_tasks()
        today = datetime.now(timezone.utc).date()
        week_end = today + timedelta(days=7)

        groups = {"overdue": [], "due_soon": [], "upcoming": []}
        for t in all_tasks:
            entry = {
                "title": t["title"],
                "list": t["list"],
                "notes": t.get("notes", ""),
                "due": t.get("due"),
            }
            due_str = t.get("due")
            if not due_str:
                groups["upcoming"].append(entry)
                continue

            due_date = datetime.fromisoformat(due_str.replace("Z", "+00:00")).date()
            if due_date < today:
                groups["overdue"].append(entry)
            elif due_date <= week_end:
                groups["due_soon"].append(entry)
            else:
                groups["upcoming"].append(entry)

        for key in groups:
            groups[key].sort(key=lambda x: x["due"] or "9999")
        return groups

    # ── Action items ──────────────────────────────────────────────────────

    def _surface_action_items(self, schedule, unread_emails):
        context_lines = []
        for e in schedule[:20]:
            context_lines.append(f"Event: {e['title']} — {e.get('location', '')}")
        for email in unread_emails[:30]:
            context_lines.append(
                f"Email from {email.get('from', '')}: {email.get('subject', '')} — "
                f"{email.get('body_preview', '')[:200]}"
            )

        if not context_lines:
            return []

        prompt = f"""Review this context from today's calendar and unread emails. Identify any follow-ups, \
commitments, or to-dos that are implied but not already logged as a formal task. Respond with ONLY a valid \
JSON array of short strings (max 8 items, empty array if none stand out).

{chr(10).join(context_lines)}"""

        response = self.ai.messages.create(
            model=MODEL,
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return []

    # ── Junk cleanup ──────────────────────────────────────────────────────
    # "Clearly junk" = definitive machine-readable signals (List-Unsubscribe /
    # Precedence headers) — these are auto-trashed. Anything the AI merely
    # *suspects* is promotional is flagged for review rather than deleted,
    # since this briefing can run unattended.

    def _cleanup_junk(self):
        emails = self.gmail.get_recent_messages(hours=self.lookback_hours)
        result = {"trashed": [], "flagged": [], "dry_run": self.dry_run}

        for email in emails:
            if self._is_clearly_junk(email):
                self._trash(email, result, reason="Unsubscribe link / bulk mail header detected")
                continue

            try:
                classification = self._classify_junk_with_ai(email)
            except Exception as e:
                logger.warning(f"Could not classify '{email.get('subject')}' for junk: {e}")
                continue

            if classification.get("is_junk"):
                result["flagged"].append({
                    "subject": email.get("subject", ""),
                    "from": email.get("from", ""),
                    "reason": classification.get("reason", "Looks promotional"),
                })

        return result

    def _is_clearly_junk(self, email):
        if email.get("list_unsubscribe"):
            return True
        if email.get("precedence", "").lower() in ("bulk", "list", "junk"):
            return True
        return False

    def _trash(self, email, result, reason):
        entry = {"subject": email.get("subject", ""), "from": email.get("from", ""), "reason": reason}
        if self.dry_run:
            logger.info(f"[DRY RUN] Would trash: {email.get('subject')}")
        else:
            self.gmail.trash_message(email["id"])
        result["trashed"].append(entry)

    def _classify_junk_with_ai(self, email):
        prompt = f"""Is this email spam, a promotional newsletter, or junk clutter? Respond with ONLY valid JSON.

From: {email.get('from', 'Unknown')}
Subject: {email.get('subject', '(no subject)')}
Preview: {email.get('body_preview', '')[:400]}

{{"is_junk": <true or false>, "reason": <one short sentence>}}"""
        response = self.ai.messages.create(
            model=MODEL,
            max_tokens=100,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return {"is_junk": False, "reason": ""}
