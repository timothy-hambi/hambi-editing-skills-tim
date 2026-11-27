---
name: "ppm-overview"
description: PPM (Post Production Manager) skill for Hambi Media's editing team, used by Sam Lloyd as PPM and by Tim Tamon when covering as Acting PPM. It runs the PPM's planning and oversight from the Monthly editor allocation app (editors by Mon–Fri, EXT dates synced from the Notion Project Management calendar, slots linked to pipeline concepts). Every run opens with a PPM overview of EXT dates that moved, INT dates too close to or after their EXT, deliveries with nothing allocated, approved concepts not yet ticketed or planned, and editor capacity. It then makes the changes asked for, such as shifting every affected editor's INT date when a brand's EXT moves, reassigning or adding tickets, marking someone unavailable, building next month's allocation, or refreshing the concept list. Use it whenever anyone mentions the PPM role, ticket allocation, the allocation app, INT or EXT dates, editor capacity, who's on what, covering Sam, Acting PPM, concepts or buckets, or planning next month, even without saying "skill".
---

# PPM overview

The allocation lives in the **Monthly editor allocation** app. Notion is only used for the EXT calendar. This skill reads the app's data, reports what changed and what's at risk, proposes edits, and writes them back only after the user approves in chat.

Team-first rules apply to every recommendation: protect editor capacity, spread work fairly, and push back with Kind Candour when an ask doesn't fit. Any message drafted for AMs, CSs or editors is blame-neutral, conversational and motivational, and is a draft for the user to send — never sent by the skill.

Read `references/app-data.md` at the start of every run: it has the app URL, the data model and the exact tool calls.

## Step 1 — Load data (every run)

1. App data, with the Artifact tool, `action: "read_db"`, `url` = the app URL, `out_dir: /mnt/user-data/outputs/ppm/app` (read_db only saves under /mnt/user-data/outputs; delete that folder at the end of the run):
   - `tickets`, `db_op: "query"`, `query.where: [["month","eq","YYYY-MM"]]` for the current month and the next month (two calls; page with `query.cursor` if `next_cursor` comes back).
   - `ext`, `db_op: "list"` (page until done).
   - `meta`, `db_op: "list"` (gives `roster`, `extSync`, `import`).
   Keep the tool's listing text: it shows each document's **version**, which you need for `if_version` when writing.
   If `tickets` is empty and `meta/import` is missing, the one-time import hasn't run: tell the user to open the app and click **Import from Notion**, then stop.
2. EXT calendar. **Token route (preferred):** `API-query-data-source` on `18b11884-e3c9-8021-a12b-000b970904c2`, `page_size: 100`, `filter_properties: ["title","<Dates property id>"]` (or no filter_properties), filter
   ```json
   {"and":[{"property":"Key Deadline","title":{"contains":"EXT"}},{"property":"Key Deadline","title":{"contains":"Delivery"}},
           {"property":"Dates","date":{"on_or_after":"<today minus 35 days>"}},{"property":"Dates","date":{"on_or_before":"<today plus 120 days>"}}]}
   ```
   following `next_cursor`. **Connector route (fallback):** `notion-query-data-sources` SQL on the same data source with the same conditions, `ORDER BY url LIMIT 100 OFFSET n`. Either way, save the rows to `/home/claude/ppm/cal.json` as a list of `{"url": <page url>, "Key Deadline": <title text>, "date:Dates:start": <Dates start>}`.

## Step 2 — Overview (every run, before anything else)

```
python3 scripts/allocation.py overview --dir /mnt/user-data/outputs/ppm/app --cal /home/claude/ppm/cal.json --today YYYY-MM-DD --weeks 3
```

Use the UK date. Turn the output into a short reply, skipping empty sections:

0. **Calendar changes the app hasn't picked up** (nobody has opened the app since). Run `sync` (below) and apply it, then reload the app data before going further. Mirroring the calendar into the EXT row is what the hourly EXT sync does anyway, so this write doesn't need approval, but say what changed.
1. **EXT moves waiting on INT shifts.** Moves later are breathing room; moves earlier are risk. Offer to shift each one (Step 3).
2. **INT within a working day of its EXT, or after it.** A 🔴 can also mean the brand's real EXT isn't in the calendar yet (Noted Aromas C1–C7 is a known case); say which is likelier.
3. **EXT deliveries with nothing matched** — possible missed allocation, or tickets named without the brand. UGC deliveries may be handled elsewhere.
4. **Tickets not matched to any EXT** — usually a brand spelt differently from the calendar tag.
5. **Capacity** — call out only editors over 5 in a week, tickets on an Unavailable day, and editors with nothing allocated in the next two weeks.

**Manual EXTs** (maroon with a dashed yellow outline in the app) are added by Sam or Tim when a delivery date isn't in the calendar, e.g. "Pore Favor C4, C7, C8 & C10". They have `manual: true`, are never changed or removed by syncing, and a manual EXT that lists concept numbers takes priority for those concepts over any calendar EXT. Treat them as real deadlines in every check. Add one with `set` in `ext` (id `manual-` + timestamp, fields `title`, `label` = title, `date`, `manual: true`, `createdAt`, `editedBy: null`, `editedAt`) when the user asks.

Matching between tickets and EXT dates is by the brand name in the ticket text (e.g. "C2 (Superpower)" ↔ "[Superpower] EXT HP Delivery"), the same way the app does it. Aliases: FS - CG = Free Soul, SBO = Sweet Bee, Rheal - Collagen = Rheal.

End with the one or two actions that matter most, then handle what the user asked.

## Step 3 — Changes from chat

Always show a before/after table, ask for approval, then write with `action: "write_db"`, `db_op: "batch"` (max 50 writes per call), passing each document's `if_version` from the listing. If a write fails on a version conflict, re-read that document and redo the change; never overwrite someone's edit.

### An EXT date moved
- If the app already recorded it (overview section 1), run
  `python3 scripts/allocation.py shift --dir /mnt/user-data/outputs/ppm/app --today … --ext <ext id>`.
- For a manual EXT, or if the user tells you before the calendar changes, run it with `--from OLD --to NEW` (then also `update` the manual EXT's `date`), and remind them the AM should update the calendar too.
The script keeps each editor's buffer (moves INT by the same number of working days), caps INT at 1 working day before the new EXT, respects the 2-tickets-per-day limit and moves clashes to the nearest free day. Sanity-check it: if a move squeezes someone below 2 working days or lands on someone already heavy that week, suggest a swap with an editor who has room. On approval, apply the printed `writes` (they also mark the EXT move as handled, which clears the yellow ring in the app). Offer a draft Slack message to the affected editors.

### Other edits
- **Reassign / move:** `update` the ticket with `editor`, `date` and `month` (month of the Monday of that week, `YYYY-MM`). Check the 2-per-day limit and the editor's week first.
- **Add:** `set` a new document in `tickets` with a new id (`skill-` + timestamp + short suffix) and `title`, `editor`, `date`, `month`, `status: "Pending"`, `notes: ""`, `createdAt`, `editedBy: null`, `editedLabel: "Claude (ppm-overview)"`, `editedAt` (ms).
- **Remove:** only on explicit request: `delete`.
- **Unavailable:** add a ticket titled `Unavailable` for each day, then list that editor's tickets on those days and propose new homes.
- **Rename / roster changes:** the editor list is `meta/roster` (`editors: [{name, type, hidden}]`, type is `editor`, `freelancer` or `aiv`). It's easiest for the user to do this in the app's **Editors** panel; if asked here, rewrite the whole list with `set`, and when renaming also update that editor's tickets.
Every write to a ticket sets `editedBy: null`, `editedLabel: "Claude (ppm-overview)"` and `editedAt` so the app shows who changed it.

## Step 4 — Build a new month

Inputs from the user: tickets per brand (C1–Cn, by name as they should appear), editor availability, and anything fixed. Load the month's EXT dates from the calendar (Step 1).

Rules learned from Sam's November plan — confirm with the user if anything conflicts:
- INT is 2–4 working days before EXT; stagger a brand's concepts across those days.
- Spread a brand across several editors, one concept each; prefer editors who cut that brand in the last two months (check the app's earlier months).
- Normally one ticket per editor per day (the app allows two; use the second slot sparingly). Aim for 2–3 per editor per week, never over 5.
- Freelancers take paired concepts over a two-day slot, due on the second day ("Two-day slot" in notes).
- AI PROD (the AI video row) is due at least 2 working days before the matching AI edit.
- Skip weekends and UK bank holidays (25 Dec, 28 Dec 2026, 1 Jan 2027).

Present the draft as a grid per week (EXT row on top, editors in the app's roster order) with weekly totals, iterate, and only on approval write it as batches of `set` writes to `tickets`. Tell the user to open the app's next month to check it.

## EXT sync only (on request)

EXT dates sync hourly through a Cowork scheduled task using the Notion token (the owner's machine must be on). The app can't sync silently on its own: the organisation requires an "Allow" click for every token call from an artifact. If the last sync is over 90 minutes old, the app flags it on its status line. The **Sync EXT dates** button tries the token first (one Allow click in Claude Desktop) and falls back to the connector in a browser.

When the prompt is "sync the EXT dates into the allocation app", skip the overview and do only this:

1. Load the EXT calendar with the **token route** (Step 1, item 2). If the token tools aren't available, stop and say so in one line: the app's **Sync EXT dates** button is the manual fallback through the connector, so don't use the connector here.
2. `read_db` the app's `ext` collection (`db_op: "list"`, `out_dir: /mnt/user-data/outputs/ppm/app`).
3. `python3 scripts/allocation.py sync --dir /mnt/user-data/outputs/ppm/app --cal /home/claude/ppm/cal.json --today YYYY-MM-DD`, then apply the printed `writes` with `write_db` `db_op: "batch"` (max 50 per call). It always stamps `meta/extSync`, so the app shows when it was last synced even when nothing changed. Moved dates get `prevDate` and `moveHandled: false`, which puts the yellow ring on them in the app; don't shift any INT dates in this mode.
4. Reply in one or two lines: how many EXT entries were added, moved or removed, and name any moved ones. Delete `/mnt/user-data/outputs/ppm` afterwards.

## Step 5 — Refresh the concept list (bucket split)

Runs when the prompt says "refresh the concept list" or "refresh concepts for <client>" (the app's **Refresh concepts** button copies these), and as part of the scheduled 12AM PH run. It mirrors Notion into the app's `concepts` collection, so it needs no approval; report the summary afterwards.

Concepts are what the app's **Linked concept** dropdown shows. A slot linked to a concept is **Ready** once the concept is ticketed and **Pending** while it's approved but not ticketed; the app works that out itself from the fields below, so this refresh never touches tickets.

**Route.** Use the token (`notionApi` `API-…` tools). Without it (claude.ai in a browser), only do a one-client refresh through the connector (2 queries: that pipeline and Editor Tickets); for a full refresh say it needs Claude Desktop with the token, or do the brands in the current week until the hourly limit, then stop and list the rest.

**Who can save.** The app's owners (Sam and Tim) can save from chat. If anyone else runs it and `write_db` is refused, say so and stop; don't retry.

1. **Existing concepts and tickets.** `read_db` the app: `concepts` (`db_op: "list"`) and this month's and next month's `tickets` (`query` on `month`), with `out_dir: /mnt/user-data/outputs/ppm/app` (read_db only saves under /mnt/user-data/outputs; delete that folder when the run is done).
2. **Pipelines.** Use `references/pipelines.md`; for a one-client refresh, just that client. Find any client not listed with `API-post-search` (query "Review Pipeline", `filter: {"property":"object","value":"data_source"}`), and note new ones in the summary.
3. **Concepts per pipeline.** `API-query-data-source` on each pipeline, `page_size: 100`, following `next_cursor`, with
   ```json
   {"and":[{"property":"ac%5D%3B","select":{"equals":"Video"}},
           {"property":"FynO","select":{"equals":"HP"}},
           {"timestamp":"created_time","created_time":{"on_or_after":"<today minus 45 days>"}}]}
   ```
   and `filter_properties: ["title","zrYQ","%5E%7CF~","r%7DEs","%7BJRu","dq%5EQ"]` (Concept, Status, Approved, Ticket created?, Campaign, Concept #). The filter uses property **IDs**, not names, because pipelines don't all name the columns the same way: Biomel's older template calls the Video/Image column "Ad Format" and uses "Format" for creative styles such as "Format - High Production", but the IDs (`ac%5D%3B` for the Video column, `FynO` for Ad Type) are the same in every pipeline, so one filter covers both templates. These IDs are shared by the pipeline template. If a pipeline rejects the filter or returns none of them, query it once without `filter_properties` and read the same properties by name. UGC and design concepts are left out on purpose: UGC tickets aren't planned (they come from unreliable creators or raw-footage edits), and design comes later.
4. **Editor ticket links (optional, skip if the run is getting long).** One `API-query-data-source` on Editor Tickets (`1d011884-e3c9-8118-98e5-000b8f796b3e`) for Type "Net new - Editor" or "Iteration - Editor" created in the last 90 days, `filter_properties: ["title","zrYQ","eLK_"]`. Map each row's Concept mention (`mention.page.id`) to that row's url, Status and first assignee name.
5. **Build records.** One per pipeline concept, written to `/home/claude/ppm/concepts_new.json` as a JSON list:
   `id` (pipeline page id), `client` (name from pipelines.md), `campaign` (first Campaign value, e.g. "CM3"), `concept` ("C" + Concept #, or the `[C9]` in the title), `conceptNum`, `title` (plain text), `url` (`https://app.notion.com/p/<id without dashes>`), `approved`, `ticketCreated`, `pipelineStatus`, `editorTicketUrl`, `editorTicketStatus`, `editorTicketAssignee` (the last three null when there's no editor ticket). "Ticket created?" is ticked automatically by the Create ticket button, which only works once Approved is ticked, so it's reliable; an editor ticket found in step 4 with the box unticked means the ticket was made by hand: keep the link and mention it.
6. **Diff and save.**
   ```
   python3 scripts/concepts_diff.py --existing /mnt/user-data/outputs/ppm/app/concepts --new /home/claude/ppm/concepts_new.json --clients ALL --tickets /mnt/user-data/outputs/ppm/app/tickets --by "Tim (ppm-overview)"
   ```
   (`--clients "Superpower"` for a one-client refresh, so only that client's stale concepts are removed.) Apply each printed batch with Artifact `write_db`, `db_op: "batch"`. Pass `if_version` for documents you read in step 1 (versions are in the read listing); new documents need none.
Pipeline responses are large (about 1 KB per concept), so in one chat cover at most about 10 pipelines; if more are left, save what's done (with `--clients` set to the ones covered) and list the rest for the next run.
7. **Reply** with the script's summary: concepts per bucket, newly ticketed (their slots just turned Ready), and approved concepts not in the plan yet. Those last ones are the chase list once their EXT gets close.

## Backups
Remind the user once a month to use **Export month (CSV)** in the app. If asked, save the export (or the read_db files) to Notion or Drive as a static record.

## Output style
Brief and production-ready. Lead with what needs a decision. Tables for change sets and grids; prose elsewhere. Change only what's asked.
