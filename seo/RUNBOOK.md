# VALUERAQ daily SEO run: runbook

This file is the full instruction set for the scheduled daily run. Follow it exactly.
The owner (Naveed) is not technical and is not watching. Never ask him a question
during a run; decide, and write what you decided in the day's report.

## 0. Ground rules

- Repository: `naved170-coder/Valueraq`, branch `main`. Render deploys `main` automatically (1 to 2 minutes).
- You write files and push. You never log in to the website and never need a password or API key.
- If the tests, the SEO audit or `seo-check` fail and you cannot fix it, push nothing. Stop and report in your final message.
- Never edit: `content/pages/` (terms, privacy, refund, cookie, disclaimer and the rest), prices, fees, `app/` code,
  or anything about commission. If one of those looks wrong, add a line to `notes` in the report.
- US English, US dollars, written for a US reader first. Plain words. Short paragraphs.

## Always leave a trace

Whatever happens after the stop checks in section 1, the run must end by pushing `seo/runs/<run date>.json`.
If you stop early (a gate fails, a page cannot be finished, research is blocked, anything), push only that report file with
`"status": "failed"`, a plain-English `"summary"` saying what stopped you, the `tasks` you did finish, and nothing else.
A silent run is the one outcome that is never acceptable: the owner and the morning self-check rely on this file.

## 1. Start

```
git clone https://github.com/naved170-coder/Valueraq.git && cd Valueraq   (or git pull if already present)
pip install -r requirements.txt --break-system-packages
```

Read `seo/config.json`. If `active` is false, stop: the run is switched off.
If today's date in Pakistan time is before `start`, stop without changing anything.

Work out the run date: today's date in Pakistan time (UTC+5). If `seo/runs/<run date>.json` already exists, stop:
today's run is done (this is the guard against publishing twice).

## 2. Pick the work

Open `seo/calendar.json`. Every run writes **one long article and three reference pages** (glossary terms or
question pages). Choose them like this:

1. **The article:** the first article in calendar order that is not yet written and that you can write properly.
   If an article topic is blocked (needs a source you cannot open, or duplicates an existing page), skip it, note why,
   and take the next article further down the calendar. Never fill the article's place with a reference page.
2. **The reference pages:** the first three unwritten reference pages in calendar order that you can write properly.
3. A topic skipped in two runs is moved to the end of `seo/calendar.json` by you, with a note in the report, so it
   stops blocking the queue. A duplicate topic is removed and replaced with a new topic from `seo/keywords.json`
   after the duplicate check.

Never write more than four pages in one run. Before choosing release times, list the `publish_at` values already used
by existing pages: never reuse one, and never put more than four pages on one Pakistan date. The article takes the
6:00 am Pakistan slot when it is free.

After day 30 of the calendar (or from `reduce_after` in config.json), write only the first two pages per day
(one article, one reference page) from the next calendar the monthly run prepares. If the calendar is used up,
write nothing new, say so in `notes`, and still write the report.

### On the 1st of the month: content refresh

On the 1st (Pakistan date), write only the first two missing pages of the day (the article and one reference page), then:

1. Refresh up to five existing pages under `content/guides/` or `content/glossary/`, oldest `updated` date first:
   re-open the cited sources, correct anything out of date, fix broken links, improve internal links to newer pages,
   check every multiple still matches `app/valuation.py`, and set `updated` to today. Do not change the address, the title's meaning or `publish_at`.
2. Never refresh a page that names a competitor or its fees (for example `valueraq-vs-flippa`, `valueraq-vs-acquire`).
   Open the competitor's own pricing page, and if anything differs from our page, describe the difference in `notes` for the owner.
3. Record each refreshed page in the report with `"action": "refresh"` and a `note` saying what changed, and add `refresh` to `tasks`.
4. If fewer than 30 unwritten days remain in `seo/calendar.json`, add new days in the same format. Run the duplicate check
   in section 3 on every new topic against existing pages and against the rest of the calendar before adding it.

### Every day: improve four existing pages from saved competitor research

`seo/serp/` holds one file per existing page (`<kind>-<slug>.json`), collected in sessions with the owner: the search,
the strongest competing pages, what they cover (`studied`) and our gaps (`gaps`). After writing the day's new pages:

1. Take FOUR files whose `applied` is `null`: the first two `guides-` files and the first two `glossary-` files
   (after those run out, take four from whichever remain; `tools-` and `calculators-` first if any are unapplied).
   Write and push the day's report file before starting this step, so a long run never loses the record.
   Skip `queue.json`. Skip a page that names a competitor or its fees.
2. Open our page and add what the `gaps` list asks for, so the page answers the search better than the pages studied:
   tables, worked examples, checklists, FAQs, clearer first lines. Keep everything already true on the page.
3. Figures: use only figures from `app/valuation.py`, the methodology page, the page itself, or a source in
   `seo/sources.json` (quote it as written there and add it to the page's Sources). A figure that appears only in a
   `studied` entry is a competitor's claim: do not use it. Never name the studied sites or copy their wording.
4. Rewrite `meta_title` and `meta_description` to win the click (the goal is a higher click rate): advertise what the
   page now has that the competing pages lack (for example "Value Table", "Worked Example", "Free Checklist",
   "No Sign-Up"), follow the title rules in section 6, and make them clearly different from the competitor titles in
   the file (`titles`, when present). Do not change the address, `publish_at` or the main keyword. Set `updated` to today. Run the editorial review
   (section 6) on the changed page; it must still score 8.5 or more, or undo the change.
5. In the file set `"applied": "<today>"` and `"applied_note": "<one line: what was added>"`. Record each page in the
   report with `"action": "improve"` and add `improve` to `tasks`. If no unapplied files are left, say so in `notes`
   and still add `improve` to `tasks`.

### Search figures

Read the website's daily ranking summary with the Render tools: `list_logs` on service `srv-dav6fknpn0mc73aclre0`,
workspace `tea-d8cutaurnols739us400`, text `rankings-snapshot`, last 2 days; parse the JSON after `rankings-snapshot `.
Use its `new` searches and the queries in `actions` to choose secondary keywords for today's pages: prefer real
searches the site already appears for. Do not use WebFetch for the website's own data. If it cannot be read, carry on.

## 3. Before writing each page: duplicate check

List `content/guides/` and `content/glossary/`. If an existing page answers the same search question, do not
write the page. Record it in the report as `"action": "skipped"` with the overlapping path. Otherwise record
`"duplicate": "pass (closest: /guides/x/, /glossary/y/)"`.

## 3b. Before writing each page: compare the top results

Every new page must be more useful than the pages already ranking for its main keyword.

1. Run `ls seo/serp/ | grep '^new-'` and look for `new-<slug>.json` with the page's exact slug from the calendar (also check `seo/serp/queue-new.json`, where `collected` marks topics that have a file) (competitor research saved in a session with the owner for upcoming
   calendar topics). If it is there, read `studied`, `gaps` and `titles` (competitor titles, when present) and plan the page, including a `meta_title` and `meta_description` that promise what the competitors' titles don't, to cover everything the top pages
   cover, plus at least two things they lack (a worked example with real arithmetic, a comparison table, a checklist,
   a clearer direct answer, FAQs they skip).
2. If there is no file (topics marked `collected` in `seo/serp/queue-new.json` have one) and WebSearch works in this run, search the main keyword, open the strongest 3 to 5 relevant
   results (skip spam and thin calculator pages), save what they cover and the gaps in `seo/serp/new-<slug>.json`
   in the same format, then plan the page as above.
3. If neither is possible, write the page as usual, set `"serp": "missing"` for it in the report, and add its slug and
   main keyword to `seo/serp/queue-new.json` so the owner's next session collects the research; the page is then
   improved later through the daily improvement step (its file will be saved as `guides-<slug>.json` or
   `glossary-<slug>.json`).
4. Competitor pages are for finding gaps only: never use their figures (unless the source is in `seo/sources.json`),
   never copy their wording and never name them on the page.
5. Never mark a page `missing` without running that `ls` check first; `seo-check` now fails if a report says `missing` while the file exists, and nothing can be pushed until the page is rewritten with it. In the report, record for each new page `"serp": "used"`, `"serp": "searched"` or `"serp": "missing"`, and add
   `serp_compare` to `tasks` when every new page has `used` or `searched`.

## 4. Research

- Use WebSearch and WebFetch. Open every source you rely on. Cite it with a link in the page.
  Prefer primary and high-authority sources: SBA.gov, IRS.gov, SEC.gov, Investopedia, AICPA, university pages,
  Apple, Google, Shopify, Amazon and Stripe documentation.
- No invented statistics, averages, "studies show", or market sizes. If you cannot open a source for a number, leave the number out.
- Multiples: quote only VALUERAQ's own default assumptions. Read them from `app/valuation.py` (`BASE`) and
  `content/pages/methodology.md`, and describe them as "VALUERAQ's default range", never as market data.
- Describe VALUERAQ accurately: six free valuation tools, three calculators, free listings, a marketplace with messaging.
  Check `content/pages/fees.md` and `content/pages/how-it-works.md` before stating anything it offers. No guarantees of results.

### When web research is not available

Scheduled runs are sometimes refused by WebSearch and WebFetch. That is not a reason to stop. Then:

- Cite only sources listed in `seo/sources.json`, and quote only the exact `quotes` given there (paraphrase `facts`).
- Every number must come from those sources, from `app/valuation.py`, or from your own worked arithmetic.
- Prefer topics in the calendar that these sources and the methodology can support well. If a topic needs a source you
  do not have, skip it this run, take the next calendar topic, and say which one you skipped in `notes`.
- If you do manage to open a new source, add it to `seo/sources.json` with its exact quotes.

## 5. Write

Article (`content/guides/<slug>.md`), 1,500 to 2,500 words. Front matter:

```
---
title: <as in the calendar>
meta_title: <60 characters or fewer, unique>
meta_description: <120 to 158 characters, unique>
h1: <title>
section: <section from the calendar>
cluster: <cluster from the calendar>
order: 60
page_type: article
answer: <one or two sentences that answer the search question directly>
keywords: <primary keyword first: it becomes the page's target in Admin → Rankings>, <secondary keywords actually used>
published: <the Pakistan date the page goes live>
updated: <same>
publish_at: <release time in UTC, see section 7>
image: /static/img/articles/<slug>.png
image_alt: <what the image shows, 8+ characters>
score: <editorial score, section 6>
related: <4 to 6 existing paths, comma separated>
cta: <tool_link from the calendar>
cta_text: <one soft sentence>
---
```

Body, in this order: `## Key takeaway`; the main sections with H2 and H3 headings; at least one comparison table;
one worked example with the arithmetic shown; one or two charts made with `scripts/seo_image.py bar` that show only
figures stated in the text; `## Frequently asked questions` with 3 to 5 `###` questions; `## Sources` listing the links.
Link in the text to the matching tool, to 3 or more related guides or glossary pages, and to `/methodology/` when a multiple is mentioned.

Reference page, 300 to 600 words, `page_type: reference`, one featured image, no charts needed:

- Glossary term → `content/glossary/<slug>.md` with `title`, `term`, `aliases`, `meta_title`, `meta_description`, `h1`,
  `definition` (one sentence), `cluster`, `related`, `updated`, plus `page_type`, `keywords`, `publish_at`, `image`, `image_alt`, `score`.
  Sections: How it works, Example (with numbers), Why it matters in a valuation, Related terms.
  Copy the shape of `content/glossary/earnout.md`.
- Question answered → `content/guides/<slug>.md` with `section: Quick answers`, same front matter as an article,
  a direct answer first, then the detail, then a 2 to 3 question FAQ.

Images for every page:

```
python scripts/seo_image.py feature --slug <slug> --title "<title>" --label "<Guide|Glossary|Quick answer> · <Topic>"
python scripts/seo_image.py bar --slug <slug> --name <short-name> --title "<chart title>" --unit "x" --data "A=1,B=2"
```

Paste the lines each command prints. Never use an outside image, a stock photo or an AI image service.

Google title and description (written to earn the click, never to mislead):

- `meta_title` (60 characters or fewer): start with the exact search the page targets, then a reason to click:
  a question the searcher is asking ("What Is My Site Worth?"), a number ("7 Real-World Examples", "4 Methods"),
  or a bracket that states what they get ("(Free)", "(Worked Example)", "(Checklist)"). No brand name needed.
- `meta_description` (120-160 characters): first sentence answers the search or states the key figure from the page;
  second sentence says what they get (worked example, checklist, free tool, about a minute, no sign-up); use "you/your".
- Every claim must be true of the page and the site: only figures the page itself states, presented as a "common
  range" or "starting range", never as a promise. No "guaranteed", "best", "#1", fake urgency or clickbait.
- Never give two pages the same main search in their titles; check `seo/keywords.json` and existing titles first.
- The word "Free" (we run no paid ads, so the search result must say it): only where something on the page is
  really free and is what the searcher wants.
  - Calculator or tool pages: title starts with "Free" ("Free Website Valuation Tool: ...") and the description
    starts with "Free:".
  - Marketplace and selling pages: "Free Listing, No Commission" early in the title; "Free to list, free to
    contact sellers, no commission" in the description.
  - Guides: no "Free" in the title. If the page links to a free tool or calculator, end the description with
    "Free calculator included." (or "List free, no commission." for selling guides) when it fits in 158 characters.
  - Glossary pages: no "Free" in title or description.
  - Write "Free", never "FREE".

Banned: "in today's fast-paced world", "delve", "unlock", "game-changer", "ever-evolving", "look no further",
and any sentence that says nothing. No year in the page address.

## 6. Editorial review (a separate pass, after writing)

Re-read each page as a strict editor and score 0 to 10 on each point, then average to one decimal:

1 matches the search intent · 2 original value (examples, workflows, numbers) · 3 facts checked · 4 authoritative sources cited ·
5 no filler · 6 natural keyword use · 7 accurate about VALUERAQ · 8 clear structure · 9 internal links ·
10 external links to high-authority sources · 11 shows real industry knowledge · 12 images relevant with alt text ·
13 readability · 14 soft, relevant call to action · 15 meta title and description compelling and within length.

- Below 8.5: rewrite once and score again. Still below 8.5: keep the page but add `hold: yes` and
  `hold_reason: Scored <n> after one rewrite: <weakest points>`.
- Automatic reject (delete the page, record as skipped): an invented fact or feature, a guaranteed outcome, a duplicate topic, a broken image.

Always add `hold: yes` with a plain-English `hold_reason` when the page: names a competitor or its fees or features;
states tax or legal rules for a specific country; mentions VALUERAQ's own prices or commission beyond linking to /fees/;
or is marked `"hold": true` in the calendar. Held pages are hidden until the owner presses Approve in Admin → Approvals.

## 7. Release times

Pages go live the day after the run, Pakistan time, one every six hours, in calendar order.
For run date D (Pakistan), use these `publish_at` values:

| Order | Pakistan time | publish_at (UTC) |
|---|---|---|
| 1 | D+1, 12:00 am | `<D>T19:00Z` |
| 2 | D+1, 6:00 am | `<D+1>T01:00Z` |
| 3 | D+1, 12:00 pm | `<D+1>T07:00Z` |
| 4 | D+1, 6:00 pm | `<D+1>T13:00Z` |

## 8. Gates (all must pass before pushing)

```
python manage.py seo-check          # 0 problems
python -m unittest tests.test_app   # all pass
python manage.py audit              # 0 critical, 0 warnings
```

A page may only link to pages that are already live or that go live before it; `seo-check` enforces this, so order the release times accordingly or leave the link out.
Also check every internal link you wrote points to a page that exists, and that every external link opened for you during research.

## 9. Report file

Write `seo/runs/<run date>.json`:

```
{
  "summary": "One plain sentence: what was written and what needs the owner.",
  "model": "<model that ran>",
  "items": [
    {"path": "/guides/<slug>/", "action": "new", "type": "Article", "score": 9.1,
     "duplicate": "pass (closest: /guides/x/)", "images": "1 featured, 2 charts",
     "keywords": ["primary", "secondary"], "note": ""}
  ],
  "tasks": ["duplicate_check", "research", "article", "reference_pages", "images", "editorial_review", "gates", "scheduled", "link_check", "report"],
  "checks": ["Tests: 111 passed", "SEO audit: 0 critical, 0 warnings", "Internal links: 0 broken", "External links: 9 opened, 0 broken", "Live check of yesterday's pages: 4 of 4 load, images load"],
  "notes": ["Anything the owner should know or do, in plain words. Empty list if nothing."]
}
```

`action` is `new`, `refresh`, `fix` or `skipped`.

`tasks` drives the Admin → Task data checklist (green tick = done). List a key only if you really did that task in this run:
`duplicate_check`, `research`, `article`, `reference_pages`, `images`, `editorial_review`, `gates`, `scheduled`,
`link_check`, `report`, and `refresh` (1st of the month only). A key you leave out shows as a red cross.

## 10. Live check

The website opens each released page and its image by itself and ticks "Pages and images checked on the live site" in
Task data. You do not need to fetch pages. If a page you wrote earlier shows as failed there, fix it in this run.

## 11. Push

```
git add -A content seo app/static/img/articles
git commit -m "SEO run <run date>: <n> pages"
git push origin main
```

Then confirm the push reached GitHub (`git log origin/main -1`). If the push is refused, do not retry in a loop:
finish with a final message that says "PUSH FAILED" and why. The website shows the owner an alert when a day has no report.

## 12. Final message

Three lines at most: pages written, pages held for approval, anything that failed.
