# Notes check

A daily accountability check. Every editor ticket due this week should have a fresh update (an ETA or context) in its Notes comments. Tickets with an update are summarised. Tickets without one are flagged to Tim with a ready-to-send Slack nudge.

It works from the Query A snapshot after the shared scope filters in SKILL.md. Dates use the report day.

## Contents

- How "new" updates work
- Extra scope filters
- Classify each this-week ticket
- Draft nudges
- Older overdue footnote
- On-demand use

## How "new" updates work

Editors don't type into the Notes text. They leave **Notion comments anchored on the Notes property**. Fetch them per ticket with `notion-get-comments`. Each discussion has `property-name="Notes"`, and each comment has an author (`user-url`) and a `datetime` in UTC. Comments are the only signal. Ignore the Notes text value.

Fetch comments only for this-week tickets. Comment fetches don't use the query allowance.

**Lookback window.** A comment is new if its datetime falls inside it:

- Wed to Sat runs: since 00:00 Asia/Manila the previous day (24 hours).
- Tuesday run: since 00:00 Asia/Manila the previous Saturday. That covers UK Friday evening, the weekend and Monday.
- On demand: since the start of the last scheduled run, unless Tim gives a window.

Comments by Tim don't count as an editor update, because he may have been the one chasing. Comments by anyone else (editor, Senior Editor, CS, AM) do count. Name the author.

## Extra scope filters

On top of the shared filters:

1. **Status** is Editor Ticket, Active, Needs INT Amends or Needs EXT Amends. Everything else is out, including SE Review, HM Internal Review, Client Review and On-Hold.
2. **Tim's own POD 6/7 edits are out.** Drop tickets where POD is "POD 6" or "POD 7" and Assigned to includes Tim. POD 6/7 tickets assigned only to other editors stay in.
3. **Split by due date:**
   - **This week**: due Monday to Sunday of the report day's week. When the report day is Friday (the Saturday run), also include tickets due the following Monday.
   - **Older overdue**: due before that Monday. These go in the footnote only.
   - Tickets due later than this week, or with no due date, are out of the Notes check.

## Classify each this-week ticket

- **Updated, new ETA**: a new comment states or changes a delivery, send or SQ date. Capture the new date and compare it with the Due date. If it's later than the Due date, mark it **ETA slip**.
- **Updated, context only**: a new comment gives progress, a blocker or a dependency (footage, VO, AI production, client feedback) but no date. Summarise it in one line.
- **No update**: no new comment in the window. Quote the latest older comment with its date so Tim has context, or say "no notes ever".
- **Unassigned**: no Assigned to. Flag it separately, because there's no one to nudge.

## Draft nudges

For every editor with one or more **No update** this-week tickets, create one draft in their DM with `slack_send_message_draft`. Find their Slack user ID with `slack_search_users` by name or email.

- Drafts only. Never use `slack_send_message` to an editor unless Tim says to send in that moment.
- Older overdue tickets don't get nudges.
- No nudge for Jelix Organista.

Tone: Kind Candour, blame-neutral, conversational and short.

```
Hey <first name>! Quick check-in on <this one / these>:
• <Client> <Concept/ticket link> (due <Day DD>)
Could you drop a quick update in the Notes comments with where it's at and your ETA? Shout if anything's blocking you and I'll help clear it. Thanks!
```

- If `attached_draft_exists` comes back, don't overwrite the draft. Paste the nudge text under that editor in Tim's checklist instead.
- If an editor can't be found in Slack, say so in the checklist.

## Older overdue footnote

For visibility only. Don't fetch comments, classify or draft nudges for these. Group by month due, oldest first, one compact line per ticket:

```
*Older overdue (<N>)*: still in Editor Ticket / Active / Needs INT / Needs EXT Amends with a due date before this week

*August*
• <Editor or Unassigned>: <Client> <Concept or 'Untitled'> · <Status> · due <DD Mon> (<X>d overdue) · <ticket link>
*September*
• ...
```

In the daily run this is the last threaded reply. If there are none, skip it.

## On-demand use

When Tim asks for the Notes check on its own in chat:

- Show the checklist and the older overdue footnote in chat, in this order: No update, ETA slips, Updated, Unassigned / data issues, Older overdue.
- Ask before creating drafts.
- If Tim then says "send them", send the nudges with `slack_send_message` to each editor and delete the matching drafts (`draft_id`).
- If he asks for it in Slack too, use the daily-run DM format from SKILL.md with only the Notes check sections.
