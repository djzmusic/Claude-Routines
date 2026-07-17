# Email Cleanup & Priority Button

One button that scans the last 24 hours of email across Gmail and Office 365, trashes junk and anything with an unsubscribe link, and ranks your business emails by priority.

It also includes a **Morning Briefing** page (`/briefing`) that pulls together your upcoming Google Calendar events, unread Gmail triaged by urgency, Google Tasks, and AI-surfaced action items — plus the same junk cleanup, run on demand.

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

### Morning Briefing (`/briefing`)

| Section | Source | Notes |
|---------|--------|-------|
| Schedule | Google Calendar | Flags events whose title/description implies prep is needed |
| Important Emails | Gmail unread | AI-triaged into Urgent / Important / FYI |
| Google Tasks | Google Tasks | Grouped into Overdue / Due Today-This Week / Upcoming |
| Action Items | Calendar + unread email | AI-surfaced follow-ups that aren't formally logged yet |
| Junk Email Cleanup | Gmail | Header-confirmed junk (`List-Unsubscribe`, `Precedence: bulk`) is auto-trashed; anything the AI only *suspects* is junk is flagged for your review, not deleted |

There's no connected messaging platform in this app yet, so "Messages Requiring Response" isn't included — that section only makes sense once a Slack/Teams-style client is wired up.

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
3. Go to **APIs & Services → Library** → search "Gmail API" → **Enable**
4. Go to **APIs & Services → Credentials → + Create Credentials → OAuth client ID**
5. Application type: **Desktop app** → Create
6. Click the download button (⬇) → save the file as `credentials_gmail.json` in this folder
7. Run the setup script:
   ```bash
   python setup_gmail.py
   ```
   A browser window will open — sign in and click Allow.

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

### Step 6 — Connect Google Calendar & Tasks (for the Morning Briefing)

1. On the same Google Cloud project as Step 4, go to **APIs & Services → Library** and enable the **Google Calendar API** and **Google Tasks API**
2. Run the setup script:
   ```bash
   python setup_google_calendar_tasks.py
   ```
   A browser window will open — sign in and click Allow.

---

### Step 7 — Run the app

```bash
python app.py
```

Then open your browser to: **http://localhost:5001**

Click the big **Clean My Inbox** button, or go to **http://localhost:5001/briefing** for the Morning Briefing. Done.

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
├── app.py                          # Web server (Flask)
├── email_processor.py              # Cleanup/priority logic + Claude AI classification
├── briefing.py                     # Morning Briefing aggregation + Claude AI triage
├── gmail_client.py                 # Gmail API wrapper
├── outlook_client.py               # Microsoft Graph API wrapper
├── google_calendar_client.py       # Google Calendar API wrapper
├── google_tasks_client.py          # Google Tasks API wrapper
├── setup_gmail.py                  # One-time Gmail authorization
├── setup_outlook.py                # One-time Outlook authorization
├── setup_google_calendar_tasks.py  # One-time Calendar/Tasks authorization
├── templates/
│   ├── index.html                  # The cleanup button UI
│   └── briefing.html               # The Morning Briefing UI
├── .env                            # Your secrets (never committed)
├── tokens/                         # OAuth tokens (never committed)
└── requirements.txt
```
