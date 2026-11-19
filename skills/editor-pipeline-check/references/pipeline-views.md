# Pipeline views: morning brief, deadline check, capacity report

All three work from the snapshot after the shared scope filters in SKILL.md. "Today" means the report day.

## Contents

- Overdue-eligible statuses
- Morning brief
- Deadline check
- Capacity report
- Chat output style
- Data issues worth flagging

## Overdue-eligible statuses

Only flag a ticket as **overdue** or **due today** while its Status is one of:

Editor Ticket, Active, SE Review, HM Internal Review, Needs INT Amends.

A ticket past its due date that has moved on to Client Review, Needs EXT Amends, On-Hold, Approved, Live or Archived is not overdue. It's past the stage where lateness sits with the editor, so it doesn't count against them.

## Morning brief

Covers every open ticket in the snapshot (everything except Approved and Live). Client Review, Needs EXT Amends and On-Hold tickets still show for visibility. They just can't be overdue.

Flag each ticket:

- **Overdue**: due before today, and Status is overdue-eligible.
- **Due today**: due today, and Status is overdue-eligible.
- **Stuck**: Status is Needs INT Amends, Needs EXT Amends or On-Hold, whatever the due date. This is separate from overdue.
- **Notes**: anything useful in the Notes text (ETA, blocker, missing footage or VO, unclear instructions, a dependency). When Notes is empty or just the placeholder, say so, because "no one has logged an update" is useful in itself. In the daily run, the Notes check already covers this from comments, so don't repeat it.

Layout:

- Group by editor, overdue first within each group.
- Quote real Notes content, or summarise it lightly.
- When one status (for example HM Internal Review) holds a large share of the overdue tickets across many editors, call it out once as a likely review bottleneck instead of repeating it under each editor.

## Deadline check

Needs both queries. For each EXT Delivery row left after the scope filters:

1. Take its Client, and its Campaign if set.
2. Find the matching tickets in the snapshot: same Client, and same Campaign when the row has one. When the row's Campaign is blank, match on Client alone.
3. Compare the furthest Status the matched tickets have reached with the delivery date (the "Dates" column):
   - **On track**: more than 1 day remains, or the matched tickets have reached Client Review, Needs EXT Amends, Approved or Live.
   - **At risk**: the delivery date is today or tomorrow, and no matched ticket has reached Client Review, Needs EXT Amends, Approved or Live.
   - **Delayed**: the delivery date has passed, and no matched ticket has reached Client Review, Needs EXT Amends, Approved or Live.
4. A row with no matching tickets is reported as exactly that. It usually means the tickets aren't tagged with the Client or Campaign, or the work hasn't been ticketed yet. Both are worth knowing.

The snapshot only holds Approved and Live tickets due in the last 30 days. For a delivery date older than that with no matching tickets, don't call it delayed. Count these in one line: "<N> older deliveries are outside the 30-day window."

Layout: one line per brand and deadline, with the bucket, the days to or past the delivery date, and the tickets (with Status) driving the bucket. Lead with delayed, then at risk, then a short on-track summary.

## Capacity report

Group every open ticket (everything except Approved and Live) by editor. For each editor give plain ticket counts:

- active or in progress
- overdue (overdue-eligible statuses only)
- due in the next 7 days, broken out by day when that helps
- On-Hold and Amends tickets sitting with them

This is a ticket count, not an hours model. Don't use the database's Estimated Edit Hours, % Capacity Used, Capacity Remaining or Weekly Hours Available formulas. The aim is a fast read on who has headroom before a new ticket is assigned.

## Chat output style

- Lead with what needs action: overdue, at risk, delayed, no headroom.
- Keep what's fine to a summary line.
- Group by editor or by brand as described above.

## Data issues worth flagging

Mention these once, briefly, wherever they turn up:

- tickets sitting in one status for a very long time
- open tickets with no assignee or no Client
- placeholder tickets that look like they should be deleted
- "LWU" tickets with no Client relation
- open tickets still assigned to Jelix Organista
