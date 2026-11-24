---
name: "ticket-status-checker"
description: Checks which of an editor's Client Review tickets have actually been approved. Use when Tim names an editor and wants to know which of their Client Review tickets are approved, e.g. 'check [editor]'s tickets', 'what's approved for [editor]', 'status check on [editor]', 'which of [editor]'s Client Review tickets can move to Approved', 'ticket status checker', or any request to compare an editor's Client Review tickets in Editor Tickets or Editor Capacity against the original client tickets. It reads Notion through Tim's Notion token (notionApi tools) when available, so it can check every client in one run, and falls back to the Notion connector otherwise. It only reads and reports and never changes a ticket.
---

# Ticket Status Checker

Finds an editor's tickets sitting in **Client Review** on the Editor Tickets board, opens the original client ticket behind each one, and reports the Concepts whose original ticket says **Approved**. These are the tickets that have been signed off but haven't caught up on the editor board yet.

This skill only reads Notion. Don't change any status, property or comment, even if a mismatch looks obvious. Tim decides what to update.

## Where things live

- **Editor Tickets page:** https://app.notion.com/p/soarwithus/Editor-Tickets-1e411884e3c980899de6d6d2918b6733
- **Tickets data source:** `collection://1d011884-e3c9-8118-98e5-000b8f796b3e`
- **Editor Capacity view:** `view://2fe11884-e3c9-8065-855f-000c80e3751d` (grouped by `Assigned to`)
- On the editor board, rows are blank. The **`Concept`** title holds a page mention, `<mention url="...">Concept name</mention>`, that links to the **original ticket**.
- The original ticket sits in that client's **Review Pipeline** database (e.g. "[Cornish Seaweed] - Review Pipeline"). Its **`Status`** select is the one that matters.
- Ignore the editor row's `Approved` checkbox. It's ticked on most rows and doesn't reflect client sign-off.

## Pick the Notion route first

Say which route you used in the reply ("via token" or "via connector").

**Token route (preferred).** Tim's "Read Review Pipelines" integration token runs as the `notionApi` MCP server in Claude Desktop, with tools named `API-…`. If they aren't in your tool list, run a tool search for "notionApi query data source" once. These calls use Notion's public API: they **don't** touch the hourly Query Data Source allowance, so there's no client-by-client budgeting and no limit stop. Notion only allows about 3 requests a second, so make calls one after another. Never mention the hourly allowance on this route.

On the token route, steps 2 and 3 change as described in **Token route steps** below. Steps 1 and 4 are the same on both routes.

**Connector route (fallback).** Steps 2 and 3 as written, with the hourly limit rules in 3d. Use it when the token tools aren't available (claude.ai in a browser, or Claude Desktop on a machine without the token).

## Token route steps

**2T. Pull their Client Review tickets.** `API-query-data-source` with `data_source_id: 1d011884-e3c9-8118-98e5-000b8f796b3e`, `page_size: 100`, `sorts: [{"property":"Due date","direction":"ascending"}]`, `filter_properties: ["title","zrYQ","eLK_","NL%3EX","eID%5D","dFFn"]` and:

```json
{"and":[
  {"property":"Status","select":{"equals":"Client Review"}},
  {"property":"Assigned to","people":{"contains":"<EDITOR_USER_ID without the user:// prefix>"}}
]}
```

Follow `next_cursor` while `has_more` is true. From each row keep the page `url`, the due date (`properties["Due date"].date.start`), the client name (`properties["Client (Raw)"].formula.string`), and from `properties.Concept.title` the item with `type: "mention"`: its `mention.page.id` is the **original ticket** and its `plain_text` is the Concept name. A title with no mention item is the "No mention in Concept" edge case below.

**3T. Check each original ticket directly.** There's no need to find each client's Review Pipeline. For each original ticket ID, call `API-retrieve-a-page` with `filter_properties: "zrYQ"` and read `properties.Status.select.name`. If `Status` isn't in the response (a pipeline with a different property ID), call it again without `filter_properties` and read `Status` from the full properties. These calls return properties only, never the page body, so there's no context flood and no limit on how many to check. Post a one-line progress note per client only if the editor has more than about 30 tickets.

- `object_not_found` or `unauthorized` on an original ticket means the "Read Review Pipelines" integration isn't connected to that client's Review Pipeline. Check that client through the connector route instead (3b–3d), and list the pipeline in one line at the end so Tim can connect it.
- Sort into buckets and handle edge cases exactly as in step 3.

## Steps

### 1. Identify the editor

Tim gives a name (often a first name). Look the person up with the Notion search tool in user mode (or `notion-get-users`) to get their `user://` ID.

- One clear match: carry on.
- Several matches (two people with the same first name): ask Tim which one in a single short question, listing the full names.
- No match: say so and ask for the full name or email.

### 2. Pull their Client Review tickets

Query the Tickets data source in **rows mode**, because SQL mode can drop the mention link in `Concept`, and that link is the whole point.

```json
{"data": {
  "mode": "rows",
  "data_source_url": "collection://1d011884-e3c9-8118-98e5-000b8f796b3e",
  "filter": {"type": "group", "operator": "and", "filters": [
    {"type": "property", "property": "Status", "propertyType": "select", "operator": "enum_is", "value": {"type": "exact", "value": "Client Review"}},
    {"type": "property", "property": "Assigned to", "propertyType": "person", "operator": "person_contains", "value": {"type": "exact", "value": "user://<EDITOR_ID>"}}
  ]},
  "sort": [{"property": "Due date", "direction": "ascending"}],
  "limit": 100
}}
```

From each row, keep: the editor-board row `url`, the mention URL and text inside `Concept`, `Clients`, and `date:Due date:start`.

If nothing comes back, tell Tim the editor has no tickets in Client Review and stop.

### 3. Check each original ticket

By default, don't fetch the original pages one by one: each fetch loads the full script page, which floods context. Work one client at a time instead. The exception is the one-by-one fallback in step 3d, when the person chooses it.

**a. Group by client.** Group the rows by `Clients`.

**b. Find each client's Review Pipeline.** Look the client up in `references/pipelines.md` first (client page ID → pipeline data source). If it isn't listed, run one Notion search on any one of that client's Concept titles (`max_highlight_length: 0`, `page_size: 3`). Pick the result whose `id` matches the mention URL, and take its `parent_data_source_url`. Its `path` should end in "Review Pipeline". Watch for near-duplicate titles in the client's Iterations Tracker or "Creatives to review" databases. Only the ID match counts. Add any new pipeline to `references/pipelines.md` in your reply notes so Tim can save it.

**c. Query each pipeline once.** Run one SQL query per client. Pipeline `url` values are stored without `/p/` (e.g. `https://app.notion.com/3bc11884e3c980688a2de22f43585c6f`), so match on the last 32 characters:

```json
{"data": {
  "data_source_urls": ["collection://<PIPELINE_ID>"],
  "query": "SELECT substr(url,-32) AS id, \"Status\" FROM \"collection://<PIPELINE_ID>\" WHERE substr(url,-32) IN ('<id1>','<id2>')"
}}
```

The page ID is the 32 hex characters at the end of each mention URL. Querying several pipelines in one call (`query-multiple-data-sources`) isn't available on Hambi's Notion plan, so don't try it.

**d. Stay within the hourly limit (connector route only).** Every rows-mode and SQL query counts towards the workspace's hourly Query Data Source allowance, and it can run out after a couple of queries. If a query returns `usage_limit_reached`:
- Stop querying and don't retry the query.
- Report what you've checked so far, and list the clients still unchecked with the number of tickets left.
- Pass on Notion's guidance once: the allowance resets within 60 minutes, and Business includes a higher allowance. Include the "Request free trial" link from the error as a Markdown link.
- Give the person the choice, and wait for their answer before doing anything else:
  - **Wait for the reset:** they message "continue [editor]" after the hour and you resume with one query per client.
  - **Check one by one now:** you open each remaining original ticket individually. This doesn't use the query allowance, but it's slower and loads each full page. It suits about 20 tickets or fewer. For more than that, say it'll take a while and suggest waiting, but still do it if they choose it.

**Checking one by one.** For each remaining original ticket, fetch the page ID from its `Concept` mention. Read only `Status` in `<properties>` and ignore the page body. Fetch one at a time. After each client, post a one-line progress update, e.g. "Free Soul: 3 still in Client Review." Then give the full reply from step 4 for the whole editor, combining these results with everything checked by query earlier.

If an editor has more than about 15 clients in Client Review, warn before step 3 that the check may hit the hourly limit, and that they can then wait for the reset or check the rest one by one.

If step 2's result is too large and gets saved to a file, parse it with Python (`json.load`, then a regex on `mention url="..."`). The file may wrap the JSON as `[{"text": "<json>"}]`.

Sort each ticket into one bucket:

| Original `Status` | Bucket |
|---|---|
| `Approved` | **Approved** (report these) |
| `Client Review` | Still in client review |
| `Editor Ticket` | Still on Editor Ticket |
| Anything else (e.g. `Needs EXT Amends`, `Live`, missing) | Needs a look |

Edge cases:
- **No mention in `Concept`** (plain text title): search Notion for the concept title and use the result that sits in a "Review Pipeline" database. If there's no confident match, put it in "Needs a look" with the note "original ticket not linked".
- **ID not returned by the pipeline query** (moved or archived page): fetch that single page and read `Status` from `<properties>`. If that fails, put it in "Needs a look" with the reason. Don't guess the status.
- **Duplicate concepts** (two editor rows linking to the same original): report the concept once.
- **Stale originals:** if a whole client's originals still say `Editor Ticket` while the editor board shows Client Review, note it in one line. The CS may not be updating the original ticket, so "not approved" there isn't proof the client hasn't signed off.

### 4. Reply

Lead with what Tim asked for: the approved Concept names. Keep the rest to one or two lines. Use the original ticket's title as the Concept name, and link it.

```
**[Editor full name]: approved by client, still showing Client Review**

1. [Concept name](original ticket URL) · [Client]
2. ...

Still waiting: X in Client Review, Y on Editor Ticket.
Needs a look: [Concept name]: [status or reason]
Checked via token / via connector.
```

- If none are approved: "None of [Editor]'s X Client Review tickets are approved in the original ticket yet." Then the "Still waiting" line.
- Leave out the "Needs a look" line when it's empty.
- If the run stopped early: "Checked X of Y tickets (N of M clients). Still to check: [client list]." Then offer the two options from step 3d: wait for the reset, or check the rest one by one now.
- Number the approved list and list nothing else in full unless Tim asks.

## Example

**Input:** "Check Anna's tickets"

**Output:**

**Anna Regan: approved by client, still showing Client Review**

1. [UGC CM3: [C15]_[Purple]_[Supermarket breakdown]](https://app.notion.com/p/3d611884e3c980d589e7cfd2acbec490) · Cornish Seaweed
2. [[C5]_[Laundry Bundle]_[POV Un-Boxing] - K](https://app.notion.com/p/3f111884e3c980758879c34e6480d5b1) · Smol

Still waiting: 2 in Client Review, 1 on Editor Ticket.
