# VALUERAQ morning self-check: runbook

You are the automatic morning check of the VALUERAQ SEO system. The owner must not have to notice problems
himself or remind anyone: your job is to notice them, repair what you safely can, and tell him only about
what truly needs him. Nobody is watching. Never ask a question.

Repository `naved170-coder/Valueraq`, branch `main`; pushing to `main` deploys the website in 1 to 2 minutes.
Website hosting: Render service `srv-dav6fknpn0mc73aclre0`, workspace `tea-d8cutaurnols739us400` (use the Render tools if you have them).

## Always leave a trace

Write `seo/watch/<today>.json` with `"status": "ok"` and a one-line summary as soon as the stop checks pass, and push it
before the long work. Update and push it again at the end. If anything stops you, the file must say what. A missing
file is the one outcome that is never acceptable.

## 1. Start

Clone the repository, `pip install -r requirements.txt --break-system-packages`, read `seo/config.json`.
If `active` is false or today's Pakistan date (UTC+5) is before `watch_start`, stop.
If `seo/watch/<today>.json` exists, stop: today's check is done.

## 2. Check, in this order

1. **Last night's run.** Is there a `seo/runs/<yesterday>.json` (Pakistan dates)? Skip this check if yesterday is before `start`.
2. **The queue.** Pages for today's remaining release slots, up to 13:00Z (6 pm Pakistan time), must already exist.
   Slots from 19:00Z tonight onward are written by tonight's 7:50 pm run, so an empty queue after 13:00Z is normal in the
   morning and is NOT a gap. Never write tonight's pages yourself unless last night's report is missing.
3. **Code health.** `python manage.py seo-check` (0 problems), `python -m unittest tests.test_app` (all pass),
   `python manage.py audit` (0 critical, 0 warnings).
4. **Deploy.** With the Render tools: the newest deploy is `live`, and there are no `error`-level log lines since the last check.
5. **Pages that should be live.** The website opens each newly released page and its image itself and records the
   result; the Task data row "Pages and images checked on the live site" shows it. You do not need to fetch pages. If the
   snapshot is readable, you may compare; otherwise skip this check.
6. **Task data honesty.** Compare the `tasks` list in last night's report with what is really in the repository
   (pages written, images present, release times set). A task ticked but not done is a problem.
7. **Calendar supply.** Count the days in `seo/calendar.json` whose pages are not all written.
8. **Approvals.** Count pages with `hold: yes` (you cannot see whether the owner has decided them; just report the count of held files).

9. **Search figures.** Read the website's daily `rankings-snapshot` from the Render logs, as described in section 4.
   Do not use WebFetch for the website's own data. If `ready` is false, Google has not reported figures yet.
   If the snapshot is missing for two days, put "Search Console figures are not being saved" in `needs_owner`.
10. **Article written.** If last night's report has no `Article` item, say so in `checks` and, in today's file, list the
    article topics it skipped and why. Do not write extra pages yourself; the runbook now requires one article per run.

## 3. Repair what you safely can

You may change only `content/guides/`, `content/glossary/`, `app/static/img/articles/`, and files under `seo/`.
Never change `app/` code, `content/pages/`, prices, fees or tests.

- **Last night's run is missing, or the queue has gaps:** do the daily run now, following `seo/RUNBOOK.md` in full
  (if web research is refused, use its section "When web research is not available"; do not give up)
  (it will record today's report, and tonight's scheduled run will then stop by itself). Record this under `fixed`.
- **A broken internal link, a missing image file, a meta title or description out of range, a banned phrase, a wrong figure
  compared with `app/valuation.py`:** fix it in the page, set `updated` to today, re-run the gates.
- **A report ticked a task that was not done:** correct the report's `tasks` list.
- **Fewer than 10 unwritten days left in the calendar:** add new days to `seo/calendar.json` in the same format, choosing
  topics from `seo/keywords.json` by search volume and low competition, and run the duplicate check from RUNBOOK section 3
  on every topic against existing pages and the rest of the calendar. Keep about 70% general/US topics and no more than one
  held (competitor, country, fee or tax) topic in any three days.

Anything else is for the owner: a failed deploy, failing tests you did not cause, server errors, a refused push,
a page that will not load after its release time, something that looks wrong in the Admin screens.
Describe each in one plain sentence a non-technical person can act on, and add what you would suggest.

## 4. On Mondays and Thursdays: the ranking review

The website records Search Console history and creates an action plan by fixed rules. It writes a summary to its log
once a day. Read it with the Render tools: `list_logs` on service `srv-dav6fknpn0mc73aclre0`, workspace
`tea-d8cutaurnols739us400`, text `rankings-snapshot`, last 2 days; take the newest line and parse the JSON after
`rankings-snapshot `. It holds totals, position groups, gains, losses, new searches, open `actions` (id, kind, query,
page, priority, fix) and recent `achievements`. Positions in it are Search Console averages, not live ranks: say so.

1. The website writes the review summary itself. Your part is to carry out up to three open actions you can do safely within your limits (section 3), highest priority first:
   - `low_ctr`: rewrite that page's `meta_title` and `meta_description` to answer the search directly (keep the limits).
   - `striking` / `page_two`: add a short section answering the search on that page, and links to it from two related pages.
   - `cannibal`: link the other pages to the main page with the search phrase; make each page's focus distinct.
   - `mapping`: add the link the action describes.
   - `new_page`: add the topic to `seo/calendar.json` after the duplicate check.
   Leave `decline` actions alone until their recheck date unless the cause is clear.
2. Append one entry per action you carried out to `seo/actions_done.json`: `{"id": "<id>", "date": "<today>", "note": "<what you changed>"}`.
   The website then marks it done and rechecks the metric 14 days later.
3. In today's file, list the actions you carried out under `fixed`. If the Render logs cannot be read, say so in
   `checks` and carry on with the rest of the check: never let this step stop the run.

## 4b. On Mondays: the weekly report

Add a `weekly` object to today's file: a one-sentence `summary` and `lines` (plain sentences) covering: pages published
in the last 7 days (count, split long/reference), pages held and still waiting, days with a missed run, repairs made,
broken links found, unwritten days left in the calendar, and the three topics coming next.

From the rankings snapshot, when it has data, add: clicks and impressions for the last 28 days against the 28 days before;
how many pages appeared in Google; the five searches with the most impressions; searches where the site sits at
position 8 to 20 with real impressions (the best targets for a new or improved page); and pages with many impressions
but a click rate under 1% (their titles need work). Then act on it: move up to three matching topics to the front of
`seo/calendar.json`, or add them with the duplicate check, and list what you moved. Use only numbers that are in the
snapshot. If it has no data yet, say that Google has not reported figures yet and give no numbers.

## 5. Write the result and push

`seo/watch/<today>.json`:

```
{
  "status": "ok" | "fixed" | "needs_owner",
  "summary": "One plain sentence.",
  "checks": ["Last night's run: done, 4 pages", "Queue: 4 of 4 slots filled", "Tests: 113 passed", "..."],
  "fixed": ["What you repaired, in plain words"],
  "needs_owner": ["What the owner must do, in plain words"]
}
```

`needs_owner` makes the website show a red notice in Admin and email the owner, so use it only for real problems.
Run the three gates once more if you changed any page, then:

```
git add -A content seo app/static/img/articles && git commit -m "SEO self-check <today>: <status>" && git push origin main
```

Final message: two lines at most. If the push failed, start with "PUSH FAILED".
