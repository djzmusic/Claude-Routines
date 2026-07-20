# Email Cleanup & Priority Button

One button that scans the last 24 hours of email across Gmail and Office 365, trashes junk and anything with an unsubscribe link, and ranks your business emails by priority.

It also includes a **Morning Briefing** page (`/briefing`) that pulls your Google Calendar, unread Gmail, and Google Tasks into one scannable page — schedule with prep flags, emails grouped by urgency, tasks grouped by due date, AI-surfaced action items, and an automatic junk-email sweep.

## What It Does

| Action | How it decides |
|--------|---------------|
| **Trash** | Email has a `List-Unsubscribe` header, `Precedence: bulk` header, or "unsubscribe" link in the body |
| **Trash (AI)** | Claude AI determines the email is promotional/marketing |
| **High Priority** | Urgent, time-sensitive, financial, legal, or a direct client request |
| **Medium Priority** | Needs a reply or action but not urgent |
| **Low Priority** | FYI, informational updates |

Gmail gets labeled (`Priority/High`, `Priority/Medium`, `Priority/Low`, `Category/Finance`, etc.).  
Outlook gets importance flags and categories.

## Morning Briefing (`/briefing`)

Click **Generate Briefing** to pull a live snapshot:

- **Schedule** — today's Google Calendar events, with time, location, attendees, and a prep flag when the title/description implies work beforehand.
- **Important Emails** — unread Gmail, summarized and grouped into **Urgent** / **Important** / **FYI**.
- **Messages Requiring Response** — reserved for a future chat/Slack/Teams integration; always empty today since no messaging platform is wired up in this codebase.
- **Google Tasks** — grouped into **Overdue** / **Due Today or This Week** / **Upcoming**.
- **Action Items** — follow-ups Claude AI infers from today's calendar and unread email that aren't already a logged task.
- **Junk Email Cleanup** — same detection as the cleanup button. Clear junk (unsubscribe header, or high-confidence AI match) is trashed automatically; borderline AI matches are flagged for your review instead of being deleted.

Any section with nothing in it is omitted from the page.

Calendar and Tasks reuse the Gmail OAuth client by default (see Step 4 below) — just enable the Calendar and Tasks APIs on the same Google Cloud project.

---

## Setup (One Time)

### Step 1 — Install Python packages

```bash
pip install -r requirements.txt
```

### Step 2 — Create your `.env` file

```bash
cp .env.example .env
```

Open `.env` and fill in your keys (see steps below for where to get them).

---

### Step 3 — Get your Anthropic API key

1. Go to [console.anthropic.com](https://console.anthropic.com/)
2. Sign in (or create a free account)
3. Click **API Keys** → **Create Key**
4. Paste the key into `.env` as `ANTHROPIC_API_KEY=sk-ant-...`

---

### Step 4 — Connect Gmail (if you use Gmail)

1. Go to [console.cloud.google.com](https://console.cloud.google.com/)
2. Create a project (any name, e.g. "Email Cleanup")
3. Go to **APIs & Services → Library** → search and **Enable** each of: "Gmail API", "Google Calendar API", "Tasks API" (Calendar/Tasks are only needed for the Morning Briefing page)
4. Go to **APIs & Services → Credentials → + Create Credentials → OAuth client ID**
5. Application type: **Desktop app** → Create
6. Click the download button (⬇) → save the file as `credentials_gmail.json` in this folder
7. Run the setup script:
   ```bash
   python setup_gmail.py
   ```
   A browser window will open — sign in and click Allow.
8. The first time you generate a Morning Briefing, Calendar and Tasks will each open their own browser consent window using the same credentials file — click Allow once for each.

---

### Step 5 — Connect Office 365 (if you use Outlook/O365)

1. Go to [portal.azure.com](https://portal.azure.com/)
2. Search **App registrations** → **+ New registration**
   - Name: `Email Cleanup`
   - Supported account types: **Accounts in any organizational directory and personal Microsoft accounts**
   - Click **Register**
3. Copy the **Application (client) ID** → paste into `.env` as `OUTLOOK_CLIENT_ID=`
4. Copy the **Directory (tenant) ID** → paste into `.env` as `OUTLOOK_TENANT_ID=`
5. Click **API permissions → + Add a permission → Microsoft Graph → Delegated permissions**
   - Add: `Mail.ReadWrite` and `User.Read`
   - Click **Grant admin consent**
6. Run the setup script:
   ```bash
   python setup_outlook.py
   ```
   It will print a code and a URL — open the URL, enter the code, sign in.

---

### Step 6 — Run the app

```bash
python app.py
```

Then open your browser to: **http://localhost:5001**

Click the big **Clean My Inbox** button. Done.

---

## Options

Edit `.env` to change behavior:

```env
LOOKBACK_HOURS=24       # How far back to scan (default: 24 hours)
DRY_RUN=true            # Test mode — shows what would happen without moving anything
```

## File Structure

```
Claude-Routines/
├── app.py                 # Web server (Flask)
├── email_processor.py     # Cleanup/priority logic + Claude AI classification
├── briefing_processor.py  # Morning Briefing logic + Claude AI summarization
├── gmail_client.py        # Gmail API wrapper
├── outlook_client.py      # Microsoft Graph API wrapper
├── calendar_client.py     # Google Calendar API wrapper
├── tasks_client.py        # Google Tasks API wrapper
├── setup_gmail.py         # One-time Gmail authorization
├── setup_outlook.py       # One-time Outlook authorization
├── templates/
│   ├── index.html        # The cleanup button UI
│   └── briefing.html     # The Morning Briefing UI
├── .env                   # Your secrets (never committed)
├── tokens/                # OAuth tokens (never committed)
└── requirements.txt
```
