# Former Patron Win-Back Sequence (Kit)

Audience: former paid patrons with an email on file, segmented by last charge date.
Send order: `winback_hot` first, `winback_warm` 7 days later, `winback_cold` last.
Skip anyone who rejoins (Kit: stop sequence when tag `patreon_member` is added, or remove them manually).
Replace `[VIRAL MASHUP NAME]` before sending.

Links (UTM-tagged so Patreon Traffic shows the source):
- Membership page: `https://www.patreon.com/mrwiredup/membership?utm_source=kit&utm_campaign=winback`

---

## Email 1 (Day 0)

**Subject:** You used to be a patron of mine
**Preview:** Here's what's changed since you left.

Hi {{ first_name | default: "there" }},

This is Joey, Mr. Wired Up. You supported me on Patreon at some point, and I wanted to let you know what's been added since.

[VIRAL MASHUP NAME] is up in full length. It's been the most requested thing I've posted this year. Along with it: new yacht rock edits, full 30 to 60 minute mixtapes, and the catalog is now over 460 tracks.

I also rebuilt the memberships:

- $10 a month: stream everything, ad-free, 320kbps
- $15 a month: everything above, plus downloads of every mix and mashup
- $20 a month: everything above, plus merch

If you want back in, here's the link:
https://www.patreon.com/mrwiredup/membership?utm_source=kit&utm_campaign=winback

Thanks for backing me before. It made a difference.

Joey

---

## Email 2 (Day 3)

**Subject:** The full version of [VIRAL MASHUP NAME]
**Preview:** It's on Patreon, start to finish.

Hi {{ first_name | default: "there" }},

Quick one. The clip of [VIRAL MASHUP NAME] that's been going around on Instagram and Facebook is about a minute long. The full version is on Patreon, along with every other mashup I've made.

Streaming members get all of it for $10 a month. If you DJ and want the files, the $15 tier includes downloads through a monthly Dropbox link.

https://www.patreon.com/mrwiredup/membership?utm_source=kit&utm_campaign=winback

Joey

---

## Email 3 (Day 7)

**Subject:** Last note from me on this
**Preview:** Then I'll leave your inbox alone.

Hi {{ first_name | default: "there" }},

I won't keep emailing you about this. If you've been meaning to come back, the link is below. If not, no hard feelings, and thanks again for the support you gave before.

https://www.patreon.com/mrwiredup/membership?utm_source=kit&utm_campaign=winback

Joey

---

## VIP note ($100+ lifetime, tag `vip_100plus`)

Send personally from Patreon (Audience, message the person directly) instead of, or before, Email 1. Keep it short:

> Hey {{first name}}, Joey here. You were one of my biggest supporters on Patreon and I never properly thanked you. I just rebuilt the memberships and added the full version of [VIRAL MASHUP NAME]. If you ever want back in, I'd love to have you. Either way, thank you.
