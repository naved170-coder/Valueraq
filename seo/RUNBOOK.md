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

Open `seo/calendar.json`. Go through the days in order and collect the pages that are not yet present under
`content/`, in the listed order, until you have four (carry on into the next day if a day is partly written).
Write those four. Never write more than four pages in one run. Before choosing release times, list the `publish_at`
values already used by existing pages: never reuse one, and never put more than four pages on one Pakistan date.

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

### Search figures

If your instructions include a "search feed" address, fetch it with WebFetch before writing (never write the address or
its token into any file). When it has data, use `queries` to choose which secondary keywords to work into today's pages:
prefer real searches the site already appears for. If it cannot be read, carry on without it.

## 3. Before writing each page: duplicate check

List `content/guides/` and `content/glossary/`. If an existing page answers the same search question, do not
write the page. Record it in the report as `"action": "skipped"` with the overlapping path. Otherwise record
`"duplicate": "pass (closest: /guides/x/, /glossary/y/)"`.

## 4. Research

- Use WebSearch and WebFetch. Open every source you rely on. Cite it with a link in the page.
  Prefer primary and high-authority sources: SBA.gov, IRS.gov, SEC.gov, Investopedia, AICPA, university pages,
  Apple, Google, Shopify, Amazon and Stripe documentation.
- No invented statistics, averages, "studies show", or market sizes. If you cannot open a source for a number, leave the number out.
- Multiples: quote only VALUERAQ's own default assumptions. Read them from `app/valuation.py` (`BASE`) and
  `content/pages/methodology.md`, and describe them as "VALUERAQ's default range", never as market data.
- Describe VALUERAQ accurately: six free valuation tools, three calculators, free listings, a marketplace with messaging.
  Check `content/pages/fees.md` and `content/pages/how-it-works.md` before stating anything it offers. No guarantees of results.

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
keywords: <primary keyword>, <secondary keywords actually used>
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
  "tasks": ["duplicate_check", "research", "article", "reference_pages", "images", "editorial_review", "gates", "scheduled", "live_check", "link_check", "report"],
  "checks": ["Tests: 111 passed", "SEO audit: 0 critical, 0 warnings", "Internal links: 0 broken", "External links: 9 opened, 0 broken", "Live check of yesterday's pages: 4 of 4 load, images load"],
  "notes": ["Anything the owner should know or do, in plain words. Empty list if nothing."]
}
```

`action` is `new`, `refresh`, `fix` or `skipped`.

`tasks` drives the Admin → Task data checklist (green tick = done). List a key only if you really did that task in this run:
`duplicate_check`, `research`, `article`, `reference_pages`, `images`, `editorial_review`, `gates`, `scheduled`,
`live_check`, `link_check`, `report`, and `refresh` (1st of the month only). A key you leave out shows as a red cross.

## 10. Check yesterday's pages on the live site

For each page in the previous report whose release time has passed and that is not held, confirm it answers on the
live site. Try WebFetch on `https://www.valueraq.com<path>`; if fetching is refused, use the Render tools to look for that
path with status 200 in the request logs (service `srv-dav6fknpn0mc73aclre0`, workspace `tea-d8cutaurnols739us400`).
Record the result in `checks`. If you have no way to check, write "Live check: not possible in this run" and leave
`live_check` out of `tasks`; the morning self-check repeats it. If a page really does not load, say so in `notes`.

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
