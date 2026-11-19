---
name: "editor-pipeline-check"
description: "One skill for every status check on Hambi's Editor Tickets board: the scheduled 12AM PH daily run, the morning brief / pre-work update, the deadline or EXT Delivery on-track check, the editor capacity report, and the Notes check with Slack nudge drafts. Use whenever Tim asks for a morning brief, a pre-work update, how we're doing on deadlines, whether an EXT delivery is on track or at risk, who has room for a ticket, an end-of-day capacity report, a full status check, the daily pipeline check, the Notes check or Notes column checklist, or which editors haven't updated their tickets, and whenever the scheduled 12AM PH run fires. It reads Notion through Tim's Notion token (notionApi tools) when available and falls back to the Notion connector with its hourly query allowance, taking one shared snapshot per run either way. Replaces editor-pipeline-status and editor-notes-check."
---

# Editor Pipeline Check

One skill, five modes, one shared Notion snapshot. It replaces `editor-pipeline-status` and `editor-notes-check`, so the scope rules live in one place.

It only reads Notion. It never changes a ticket, and it never sends a Slack message to an editor unless Tim says to in that moment.

## Pick the Notion route first

There are two ways to read Notion. Decide at the start of every run and say which one you used in the reply or DM ("via token" or "via connector").

**Token route (preferred).** Tim's "Read Review Pipelines" integration token runs as the `notionApi` MCP server in Claude Desktop. Its tools are named `API-…` (for example `API-query-data-source`, `API-retrieve-a-page`). If they aren't in your tool list, run a tool search for "notionApi query data source" once to load them. If they're available, use them for Query A and Query B.
- These calls go through Notion's public API. They **don't** use the hourly Query Data Source allowance, so the limit guard below doesn't apply, and refreshing the snapshot is fine when Tim asks. Notion only rate-limits them to about 3 requests a second, so make calls one after another, not in a burst.
- Never mention the hourly allowance in a token-route reply.
- The token only exists in Claude Desktop on Tim's computer. A scheduled run that fires when the computer is off, or a chat on claude.ai in a browser, won't have it.

**Connector route (fallback).** The claude.ai Notion connector (`notion-query-data-sources` and friends). Hambi's Notion plan gives it a small hourly Query Data Source allowance that can run out after a couple of queries, so on this route query Notion **at most twice per run** and treat extra data source queries as off limits unless Tim asks for a refresh.

On either route these don't count towards any allowance, so use them freely: `notion-get-comments`, `notion-get-users`, single page fetches and every Slack tool.

If a token call returns `object_not_found` or `unauthorized`, the integration has lost access to that database. Switch to the connector route for that query, and tell Tim in one line which database needs the "Read Review Pipelines" connection re-added.

## Modes

Tim can ask for one mode, several, or all of them. Run only what's asked.

| Mode | Typical ask | Queries | Rules |
|---|---|---|---|
| **Daily run** | The scheduled 12AM PH task, "daily pipeline check", "full status check" | A + B | This file, plus both reference files |
| **Morning brief** | "morning brief", "pre-work update" | A | `references/pipeline-views.md` |
| **Deadline check** | "how are we doing on deadlines", "is X on track", "EXT Delivery check" | A + B | `references/pipeline-views.md` |
| **Capacity report** | "who has room", "capacity report", "end-of-day report" | A | `references/pipeline-views.md` |
| **Notes check** | "Notes check", "Notes column checklist", "who hasn't updated" | A | `references/notes-check.md` |

Read only the reference files the requested modes need.

Checking whether Client Review tickets have been approved is a different job with a different query cost. That stays with the `ticket-status-checker` skill and never runs from here.

## Dates

Tim follows UK hours from the Philippines. 12AM Manila is the end of the UK working day.

- **Report day**: the UK working day being reported on.
  - Scheduled daily run: the Manila date minus one day. A Saturday run reports on Friday, a Tuesday run on Monday.
  - On demand: the current UK date (Europe/London), unless Tim says otherwise.
- **"Today"** in every rule means the report day.
- **This week** is Monday to Sunday of the report day's week.

## Step 1: Take the snapshot

### Query A: Editor Tickets (every mode)

- Page: https://app.notion.com/p/soarwithus/Editor-Tickets-1e411884e3c980899de6d6d2918b6733
- Data source: `collection://1d011884-e3c9-8118-98e5-000b8f796b3e`

**Token route.** Call `API-query-data-source` with `data_source_id: 1d011884-e3c9-8118-98e5-000b8f796b3e`, `page_size: 100`, `sorts: [{"property":"Due date","direction":"descending"}]`, and this `filter_properties` list so each row stays small:

```
["title","zrYQ","eLK_","B%7C%5B%60","UYZW","FynO","ac%5D%3B","NL%3EX","eID%5D","%7BJRu","Pf%60A","j%40nd","dFFn"]
```

(Concept, Status, Assigned to, POD, Type, Ad Type, Format, Due date, Clients, Campaign, Priority, Notes, Client (Raw).) Run two calls, because Notion's API only allows two levels of nesting in a filter:

1. Open tickets:
```json
{"and":[
  {"or":[{"property":"Type","select":{"equals":"Net new - Editor"}},{"property":"Type","select":{"equals":"Iteration - Editor"}}]},
  {"or":[{"property":"Status","select":{"equals":"Editor Ticket"}},{"property":"Status","select":{"equals":"Active"}},
         {"property":"Status","select":{"equals":"SE Review"}},{"property":"Status","select":{"equals":"HM Internal Review"}},
         {"property":"Status","select":{"equals":"Needs INT Amends"}},{"property":"Status","select":{"equals":"Client Review"}},
         {"property":"Status","select":{"equals":"Needs EXT Amends"}},{"property":"Status","select":{"equals":"On-Hold"}}]}
]}
```
2. Signed-off tickets (deadline check and daily run only):
```json
{"and":[
  {"or":[{"property":"Type","select":{"equals":"Net new - Editor"}},{"property":"Type","select":{"equals":"Iteration - Editor"}}]},
  {"or":[{"property":"Status","select":{"equals":"Approved"}},{"property":"Status","select":{"equals":"Live"}}]},
  {"property":"Due date","date":{"on_or_after":"<report day minus 30 days>"}}
]}
```
Follow `next_cursor` while `has_more` is true. Read values from `properties`: select → `.select.name`, people → `.people[].name` (names come back directly, so no user lookup is needed), date → `.date.start`, multi-select → `.multi_select[].name`, Client (Raw) → `.formula.string` (client name), Clients → `.relation[].id` (client page IDs, for the Butter & Crust check), Concept → the title's `plain_text`. The ticket link is the page `url`. If a response is saved to a file because it's large, parse it with Python.

**Connector route.** Use the SQL below with `notion-query-data-sources`.

```sql
SELECT url, "Concept", "Status", "Assigned to", "POD", "Type", "Ad Type", "Format",
       "date:Due date:start" AS due, "Clients", "Campaign", "Priority", "Notes"
FROM "collection://1d011884-e3c9-8118-98e5-000b8f796b3e"
WHERE "Type" IN ('Net new - Editor','Iteration - Editor')
  AND (
    "Status" IN ('Editor Ticket','Active','SE Review','HM Internal Review',
                 'Needs INT Amends','Client Review','Needs EXT Amends','On-Hold')
    OR ("Status" IN ('Approved','Live') AND "date:Due date:start" >= '<report day minus 30 days>')
  )
ORDER BY due DESC
```

- The `Approved`/`Live` clause exists only so the deadline check can see deliveries that have already been signed off. **Leave that clause out when the run has no deadline check** (morning brief, capacity or Notes check on their own), so the result stays small.
- Newest due dates come first on purpose. If paging is cut short, the part that's missing is the old backlog, not this week's work.
- Results can paginate (`has_more`). Keep going until all rows are in, but treat each page as if it may count towards the allowance: if a page returns `usage_limit_reached`, stop and follow the limit guard below.
- If the query fails on the `OR` clause, run it once more with the open statuses only. In the deadline check, report any delivery with no open tickets as "no open tickets found, may already be approved" instead of "no tickets".
- If the result is too large and gets saved to a file, parse it with Python (`json.load`). The file may wrap the JSON as `[{"text": "<json>"}]`.

Column notes, confirmed on live rows:

- `Concept` (title) is often blank on real tickets. That isn't a data error. Show "Untitled".
- `Notes` (text) is usually empty or the placeholder "NOTES". Editors leave their updates as comments on the Notes property, which only the Notes check reads.
- `Assigned to` holds people from a workspace of 25+. An unfamiliar ID is usually a real editor.

### Query B: EXT Delivery view (deadline check and daily run only)

**Token route.** The public API can't read a saved view, so rebuild it: call `API-query-data-source` with `data_source_id: 18b11884-e3c9-8021-a12b-000b970904c2`, `page_size: 100` and

```json
{"and":[
  {"property":"Key Deadline","title":{"contains":"EXT"}},
  {"property":"Key Deadline","title":{"contains":"Delivery"}},
  {"property":"Dates","date":{"on_or_after":"<report day minus 30 days>"}},
  {"property":"Dates","date":{"on_or_before":"<report day plus 14 days>"}}
]}
```

Drop rows whose title contains "Design", "Script" or "Statics". The delivery date is `properties.Dates.date.start` and the client is `properties.Client.relation[].id`. If the results look different from the EXT Delivery view (missing deliveries Tim expects), say so and use the connector route for Query B next time.

**Connector route.**

- View: https://app.notion.com/p/soarwithus/18b11884e3c98071bca8fe37b9bc51b9?v=1c211884e3c98067ac32000cf33e4816
- Data source: `collection://18b11884-e3c9-8021-a12b-000b970904c2`
- Query it in **view mode** with that view URL, so it arrives already filtered to EXT Delivery rows.
- The delivery date is in **"Dates"** (SQL column `date:Dates:start`), not "Start Date" (which is blank on these rows). This column used to be called "Shoot Date".
- Each row has `Client` (relation, the same Clients database as tickets) and sometimes `Campaign` (often blank).

### Reusing a snapshot

- One snapshot serves every mode in the run. Never re-query between modes.
- Follow-up questions in the same conversation ("and who has room?") reuse the snapshot already taken, as long as it covers what's needed. Say what time it was taken. Re-query only when Tim asks for a refresh, or when a deadline check is asked for and Query B hasn't been run yet.
- Never reuse data from a different conversation or an earlier scheduled run. Statuses and dates change all day.

### Limit guard (connector route only)

If any connector query returns `usage_limit_reached`:

1. Stop querying. Don't retry.
2. Deliver every section the data in hand supports.
3. Name the sections that are missing and why, in one line each.
4. Pass on Notion's guidance once: the allowance resets within 60 minutes.
5. On a scheduled run, finish there. On demand, offer to pick up the missing sections when Tim messages after the reset.

## Step 2: Apply the shared scope filters

Apply all of these in memory to both query results, before any mode runs. Excluded tickets and rows don't appear in any count, list or roll-up.

1. **Type** is exactly "Net new - Editor" or "Iteration - Editor". Query A already enforces this. Blank or any other Type is out.
2. **Video only.** Drop a ticket if Status is "Designer Ticket", Ad Type includes "Design", or Format is "Image" or "Carousel". A blank Format is fine and isn't a reason to drop.
3. **No Butter & Crust.** Drop tickets and EXT Delivery rows whose Client is Butter & Crust (client page `3a311884e3c980e89ff9f2ffb625f3c0`), whose POD is "LWU", or whose title starts with "LWU". If an "LWU" ticket has no Client relation, still drop it and mention the mismatch once under data issues.
4. **Jelix Organista is off every team list.** He gets no editor line in any report and no nudge. If open tickets are still assigned to him, list them once under data issues as needing a new owner, so they don't go unseen.

If a ticket passes filter 1 but is unclear on filter 2 (no Format and no clear Ad Type), keep it and mark it "ambiguous" so Tim can confirm.

Mode-specific filters (for example, the Notes check leaves out Tim's own POD 6/7 edits) are in the reference files.

## Step 3: Resolve names

On the token route, `Assigned to` already includes names. On the connector route, resolve `Assigned to` IDs with `notion-get-users` before calling any ID unknown.

- Tim's Notion user ID: `0218c510-36bf-434c-967c-4c22e4e0b13d`
- Tim's Slack user ID: `U061U6AMS57`

## Step 4: Run the modes

Follow the reference file for each requested mode. Each ticket is judged from the snapshot only.

## Delivery

### On demand (any mode Tim asks for in chat)

Reply in chat. Lead with what needs action and keep fine things to a summary line. Don't post to Slack or create a Notion page unless Tim asks. For the Notes check, show the checklist in chat and ask before creating nudge drafts.

### Daily run (scheduled, or when Tim asks for the daily run)

Send one Slack DM to Tim (channel `U061U6AMS57`) with `slack_send_message`, then add the detail as threaded replies under it (`thread_ts` of the main message). On demand, show the same content in chat as well.

**Main DM**

```
*Editor Pipeline: <report day, Day DD Mon> (UK EOD)*
Snapshot <HH:MM> PH via <token/connector> · notes window since <date time> PH
<X> open tickets · <O> overdue · <B> no update · <C> ETA slips · <D> deliveries delayed · <R> at risk

*Deadlines*
• Delayed: <Client> <Campaign> · was due <DD Mon> (<N>d ago) · <tickets and their Status>
• At risk: <Client> <Campaign> · due <today/tomorrow> · <tickets and their Status>
On track: <N> deliveries

*No update, follow up* (grouped by editor)
• <Editor>: <Client> <Concept or 'Untitled'> · <Status> · due <Day DD> · <ticket link>
  last note: "<latest comment>" (<date>) / no notes ever

*ETA slips*
• <Editor>: <ticket> · due <date> → new ETA <date> · "<comment>"

*Unassigned / data issues*
• ...

In the thread: overdue and stuck by editor · capacity · updated tickets · older overdue (<N>).
Draft nudges are waiting in each editor's DM. Open Slack Drafts & Sent to review and send.
```

**Threaded replies, in this order**

1. **Overdue and stuck, by editor**: the morning brief content from `references/pipeline-views.md`. A ticket already listed under "No update" in the main DM appears here as a short line with "(also no update)", not in full again.
2. **Capacity**: one line per editor from the capacity report.
3. **Updated**: tickets with a new Notes comment, one line each.
4. **Older overdue**: the footnote from `references/notes-check.md`. Skip it when there are none.

Rules for the daily run:

- Leave out any section that's empty, and drop its mention from the pointer line.
- Keep each Slack message under about 4,500 characters. Split a long section across more replies in the same thread.
- Create nudge drafts as described in `references/notes-check.md`. Drafts only.
- If the limit guard fired, say which sections are missing at the top of the main DM.
- If the run fell back to the connector route, say so in one line at the end of the main DM, so Tim knows the token wasn't available (for example, the computer was off).
