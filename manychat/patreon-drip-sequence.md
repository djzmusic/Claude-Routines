# Mr. Wired Up — ManyChat → Patreon Drip Funnel

**Goal:** Every ManyChat subscriber gets dripped until they become a Patreon member. The moment they join, they drop out automatically.

Placeholders to swap: `[PATREON_LINK]` (use a UTM: `?utm_source=manychat&utm_campaign=drip`), `[TIER]`, `[$X]`, `[FREE_MASHUP_LINK]`.

---

## 1. The rule that shapes everything (Meta's 24-hour window)

Instagram and Facebook only let you send promo DMs **within 24 hours of the subscriber's last interaction** with you. Outside that window, ManyChat can't legally push a sales DM. So a "forever drip" in DMs alone is impossible. The fix is three lanes:

| Lane | What it does | Runs forever? |
|---|---|---|
| **A. Email drip** (ManyChat Email) | The real "constant" drip. No 24h limit. | ✅ Yes |
| **B. DM drip** | Same steps, sent only when the 24h window is open | Only while engaged |
| **C. Window re-openers** | Your daily posts + comment keywords reopen the window, which fires the next DM step | ✅ Yes, because you post daily |

**So the #1 job of the first message is to capture email.** No email = they can only be reached when they engage.

---

## 2. Setup (do once)

**Tags**
- `patreon_member` — the exit tag. Anyone with it gets nothing from this funnel.
- `drip_active`
- `email_captured`
- `drip_paused_30d` — for people who tap "not now"

**Custom fields**
- `drip_step` (Number, starts at 0)
- `last_drip_sent` (Date)
- Email (system field)

**Global rule (Automation → Rules):**
- Trigger: *Tag `patreon_member` applied* → Remove `drip_active`, set `drip_step` = 999, send the Welcome-to-Patreon message (section 6).

**Backfill existing subs:** Contacts → filter *Tag `patreon_member` does not exist* → Bulk action: add tag `drip_active`, set `drip_step` = 0, then start the flow `Patreon Drip – Entry`.

---

## 3. Auto-exit when someone joins Patreon (Zapier)

Neither ManyChat nor Patreon is connected to your Zapier yet. Connect both, then build:

1. **Trigger:** Patreon → *New Member* (or *New Pledge*)
2. **Action:** ManyChat → *Find User by Custom Field* → field: Email = Patreon member email
3. **Action:** ManyChat → *Add Tag to User* → `patreon_member`
4. *(Optional)* Gmail → notify you: "New patron from ManyChat: {{name}}"

**Backup exit (for email mismatches):** every drip message has an **"I already joined ✅"** button → asks for their Patreon email → adds `patreon_member` + pings you to verify.

---

## 4. Flow structure

Build each step as a Flow with **Smart Delays**. Before every send, put a **Condition** block:
`Tag patreon_member does NOT exist` AND `Tag drip_paused_30d does NOT exist` → continue. Otherwise → stop.

```
ENTRY (any keyword / new subscriber)
  └─ Msg 0: Welcome + free mashup + email capture
      ├─ Day 1  → Msg 1
      ├─ Day 3  → Msg 2
      ├─ Day 5  → Msg 3
      ├─ Day 7  → Msg 4
      ├─ Day 10 → Msg 5
      ├─ Day 14 → Msg 6 (last "launch" message)
      └─ EVERGREEN LOOP: every 7 days, rotate Msg E1 → E8, then repeat
```

Each message sends by **Email always** + **DM if the 24h window is open** (ManyChat handles this if you add both channels to the step; DM fails silently outside the window).

**Buttons on every message:** `Join Patreon 🔥` → `[PATREON_LINK]` · `I already joined ✅` · `Not right now` (adds `drip_paused_30d`, auto-removed after 30 days by a Smart Delay).

---

## 5. Copy

### Msg 0 — Day 0 (Welcome + email capture)
> Yo, it's Mr. Wired Up 🔌 Thanks for rocking with me.
> Here's a mashup you can't get on TikTok: [FREE_MASHUP_LINK]
> Want the stuff I *don't* post publicly? Drop your email and I'll send you the next exclusive drop before anyone else. 👇

*(Email capture block → tag `email_captured`)*

### Msg 1 — Day 1 (What Patreon is)
> Quick one — every day I post a mashup. But the extended versions, the unreleased edits, and the ones I can't post because of copyright? Those live on my Patreon.
> [TIER] is [$X]/mo. Less than a coffee. 👉 [PATREON_LINK]

### Msg 2 — Day 3 (Behind the scenes)
> Real talk: some of my best mashups never hit socials. Too long, too wild, or the label would take them down.
> Patreon is where they live. Here's what's in there right now: [list 3 recent drops]
> 👉 [PATREON_LINK]

### Msg 3 — Day 5 (Social proof)
> "[Patron quote/screenshot]" — that's from one of my patrons this week.
> The crew in there gets first listen on everything + requests. Come through 👉 [PATREON_LINK]

### Msg 4 — Day 7 (Request hook)
> Got a song combo you've always wanted to hear together? Patrons get to request mashups. I actually make them.
> Lock in your request 👉 [PATREON_LINK]

### Msg 5 — Day 10 (Objection: "Why pay?")
> "Why pay when you post free stuff every day?"
> Fair. The free stuff stays free. Patreon is for people who want MORE — full-length versions, downloads, and a say in what I make next. It also keeps me making this daily. 🙏
> 👉 [PATREON_LINK]

### Msg 6 — Day 14 (Soft urgency)
> This month's exclusive drop goes out on [DATE]. Join before then and it's yours.
> 👉 [PATREON_LINK]

### Evergreen loop (every 7 days, rotate E1–E8, repeat forever)
- **E1 – New drop:** "Just dropped [TITLE] on Patreon. 🔥 Patrons already have it 👉 [LINK]"
- **E2 – Monthly recap:** "Here's everything patrons got this month: [list]. 👉 [LINK]"
- **E3 – Request spotlight:** "A patron asked for [A] x [B]. I made it. You could be next 👉 [LINK]"
- **E4 – Behind the board:** short Ableton/CapCut clip of how a mashup gets built + "Full breakdowns on Patreon"
- **E5 – Milestone:** "We just hit [X] patrons. Help me get to [Y] 👉 [LINK]"
- **E6 – Price anchor:** "[$X]/mo = [N] exclusive mashups a month. That's [$cost] a track."
- **E7 – Personal:** "Why I started doing this daily…" (short story, soft CTA)
- **E8 – Direct ask:** "Straight up — if you've vibed with my stuff, Patreon is the best way to support it. 👉 [LINK]"

Refresh E1, E2, E5 monthly with real titles/numbers — 10 minutes a month.

---

## 6. Welcome-to-Patreon (fires on `patreon_member`)
> You're IN. 🔌🙏 Appreciate you for real.
> Your first exclusive is waiting: [LINK TO PATRON POST]
> Reply with a song combo and I'll put it on the request list.

---

## 7. Lane C — Keep the DM window open (uses your daily posting)

Every daily post on TikTok/IG/FB gets a CTA: **"Comment WIRED for the extended version."**
- ManyChat **Comment keyword trigger** → DMs the link → this reopens the 24h window → the next pending DM drip step can fire.
- Rotate keywords monthly (`WIRED`, `MASHUP`, `FULL`, `DROP`) so you can track which posts convert.
- Add the same keyword to IG Story replies and your bio link.

---

## 8. Guardrails
- Max **1 promo per 7 days** in the evergreen loop. More = unsubscribes and spam flags.
- Email footer must have unsubscribe (ManyChat adds it — don't remove it).
- Track: Patreon link clicks (UTM) and conversions per message in ManyChat Analytics. Kill or rewrite any step under 1% click rate after 30 days.
