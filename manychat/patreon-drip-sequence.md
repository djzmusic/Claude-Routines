# Mr. Wired Up — ManyChat → Patreon Drip Funnel

**Goal:** Every ManyChat subscriber gets dripped until they become a Patreon member. The moment they join, they drop out automatically.

**Patreon link (use everywhere):** https://www.patreon.com/mrwiredup?utm_source=manychat&utm_campaign=drip

Still to swap by hand: `[FREE_MASHUP_LINK]`, `[FREE_TRACK_LINK]`, `[PATREON_POST]`, `[CODE]`, `[DATE]`, `[TITLE]`, and the per-message lists/quotes.

### Live tiers (pulled from Patreon 2026-10-02)

| Tier | Price | Patrons | What they get |
|---|---|---|---|
| Free | $0 | 7,444 | Follower access, public posts |
| 4 on the FLOOR | $5/mo | 37 | 4 mashups a month, 320kbps radio quality |
| **My Entire Mash Up Catalog** ⭐ | **$8/mo** | **457** | Full HQ streaming of the entire mashup catalog (460+), favorite TikTok mashups, full-length mixtapes (30–60 min), ad-free, 320kbps |
| Mixtapes & Mash Ups | $12/mo | 134 | Full-length mixtapes (30–60 min), stream the full catalog, 4 new mashups a month |
| MP3 Downloads | $20/mo | 231 | Download every mashup and mix as MP3 via a monthly Dropbox link |

**Lead offer in the drip: My Entire Mash Up Catalog, $8/mo.** It's the most popular tier and the easiest yes. Mention MP3 Downloads ($20) as the upgrade for DJs who want files.

*Drafted but unpublished on Patreon: STREAMING $10, DOWNLOADS $15, MERCH $20, MENTORSHIP $150. Don't reference these in copy until they're live.*

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

## 4A. Tip of the funnel — Master Comment Flow (replaces the 79 one-offs)

Built from your real Yacht/Baker Street flow (2,541 sent, 59.8% CTR) + the Rhythm email ask (73% reply rate). Everything links to Patreon. Duplicate this one flow per post; only swap the keyword, song tag, and links.

```
TRIGGER: comment keyword on post/reel
  → Action: add tag [song]
  → Condition: has tag patreon_member?
       YES → "You're a patron 🙌 here's the track: [PATREON_POST]"  → END
       NO  ↓
Msg 0  "Hey! Thanks for the comment 🔌
        Tap JUST THE TRACK for the full [SONG] remix
        or GIVE ME EVERYTHING for the full catalog (460+ mashups)"
        [Just the track]                 [Give me everything] → tag hot_lead → Msg 2

Msg 1  User Input (reply type = EMAIL, save to system Email field)
       "Where should I send the full version? Drop your email 👇"
         on reply      → tag email_captured → send [FREE_TRACK_LINK]
         no reply 10m  → send [FREE_TRACK_LINK] anyway (don't lose them)
       → Msg 2

Msg 2  "You made the right move 👀 $8/mo unlocks my entire catalog —
        460+ mashups, full-length mixtapes, and I keep adding more."
        [Grab the collection] → https://www.patreon.com/mrwiredup?utm_source=manychat&utm_campaign=drip  (button click → tag clicked_offer)
        (if no email yet: repeat the email ask here, once)

SMART DELAY 23 hours   ← keeps you inside Instagram's 24h window
  → Condition: has tag patreon_member? YES → END

Msg 3  "Hope you're liking the [SONG] remixes. Rest of the collection is here.
        **DISCOUNT CODE: [CODE]**" (or drop the code line if you're not running one)
        [Yes! More please] → https://www.patreon.com/mrwiredup?utm_source=manychat&utm_campaign=drip (tag clicked_offer)

HANDOFF
  → Condition: has tag email_captured?
       YES → add tag drip_active, set drip_step = 1 → email drip (section 4B) takes over
       NO  → END (they re-enter next time they comment on any post)
```

**Why this order:** DMs only get you 24 hours, and Instagram can't message them after that. The email ask in Msg 1 is what makes the forever drip possible. At your volume (~2,500 commenters per hit post × ~70% email reply), that's ~1,700 emails from one post.

**Check before launch:**
- Use a **User Input** block with type **Email**, not a plain "waiting for text" reply. Otherwise the address isn't validated and you can't email it.
- ManyChat Email needs your sender domain verified (Settings → Email).

---

## 4B. Email drip structure (after the 24h DM window closes)

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

Days count from the handoff. Messages go by **email**. If they comment again (reopening the 24h window), the next step can also go by DM.

**Buttons on every message:** `Join Patreon 🔥` → `https://www.patreon.com/mrwiredup?utm_source=manychat&utm_campaign=drip` · `I already joined ✅` · `Not right now` (adds `drip_paused_30d`, auto-removed after 30 days by a Smart Delay).

---

## 5. Copy

### Msg 0 — Day 0 (Welcome + email capture)
> Yo, it's Mr. Wired Up 🔌 Thanks for rocking with me.
> Here's a mashup you can't get on TikTok: [FREE_MASHUP_LINK]
> Want the stuff I *don't* post publicly? Drop your email and I'll send you the next exclusive drop before anyone else. 👇

*(Email capture block → tag `email_captured`)*

### Msg 1 — Day 1 (What Patreon is)
> Quick one — every day I post a mashup. But the extended versions, the unreleased edits, and the ones I can't post because of copyright? Those live on my Patreon.
> "My Entire Mash Up Catalog" is $8/mo — 460+ mashups plus full-length mixtapes, ad-free in 320kbps. Less than a coffee run. 👉 https://www.patreon.com/mrwiredup?utm_source=manychat&utm_campaign=drip

### Msg 2 — Day 3 (Behind the scenes)
> Real talk: some of my best mashups never hit socials. Too long, too wild, or the label would take them down.
> Patreon is where they live. Here's what's in there right now: [list 3 recent drops]
> 👉 https://www.patreon.com/mrwiredup?utm_source=manychat&utm_campaign=drip

### Msg 3 — Day 5 (Social proof)
> "[Patron quote/screenshot]" — that's from one of my patrons this week.
> The crew in there gets first listen on everything + requests. Come through 👉 https://www.patreon.com/mrwiredup?utm_source=manychat&utm_campaign=drip

### Msg 4 — Day 7 (Request hook)
> Got a song combo you've always wanted to hear together? Patrons get to request mashups. I actually make them.
> Lock in your request 👉 https://www.patreon.com/mrwiredup?utm_source=manychat&utm_campaign=drip

### Msg 5 — Day 10 (Objection: "Why pay?")
> "Why pay when you post free stuff every day?"
> Fair. The free stuff stays free. Patreon is for people who want MORE — $8/mo streams the entire catalog plus full-length mixtapes, and $20/mo gets you every mashup as an MP3 download for your own sets. It also keeps me making this daily. 🙏
> 👉 https://www.patreon.com/mrwiredup?utm_source=manychat&utm_campaign=drip

### Msg 6 — Day 14 (Soft urgency)
> This month's exclusive drop goes out on [DATE]. Join before then and it's yours.
> 👉 https://www.patreon.com/mrwiredup?utm_source=manychat&utm_campaign=drip

### Evergreen loop (every 7 days, rotate E1–E8, repeat forever)
- **E1 – New drop:** "Just dropped [TITLE] on Patreon. 🔥 Patrons already have it 👉 https://www.patreon.com/mrwiredup?utm_source=manychat&utm_campaign=drip"
- **E2 – Monthly recap:** "Here's everything patrons got this month: [list]. 👉 https://www.patreon.com/mrwiredup?utm_source=manychat&utm_campaign=drip"
- **E3 – Request spotlight:** "A patron asked for [A] x [B]. I made it. You could be next 👉 https://www.patreon.com/mrwiredup?utm_source=manychat&utm_campaign=drip"
- **E4 – Behind the board:** short Ableton/CapCut clip of how a mashup gets built + "Full breakdowns on Patreon"
- **E5 – Milestone:** "We just hit 850 paying patrons. Help me get to 1,000 👉 https://www.patreon.com/mrwiredup?utm_source=manychat&utm_campaign=drip" (update the number monthly)
- **E6 – Price anchor:** "$8/mo = 460+ mashups and full mixtapes. That's under 2 cents a track."
- **E7 – Personal:** "Why I started doing this daily…" (short story, soft CTA)
- **E8 – Direct ask:** "Straight up — if you've vibed with my stuff, Patreon is the best way to support it. 👉 https://www.patreon.com/mrwiredup?utm_source=manychat&utm_campaign=drip"

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
