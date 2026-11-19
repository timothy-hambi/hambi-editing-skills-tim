---
name: edit-performance-tracker
description: Monthly report on how Hambi's HP net new edits perform once live, matching Meta ads in Foreplay to the editor who cut them via the Notion Editor Tickets export (client + CM# + concept
---

# Edit performance tracker

Produces a workbook showing, per HP net new concept, the editor(s), spend and ROAS for a date window, plus the ads that couldn't be matched and why. It's a learning and coaching tool: ROAS depends on script, offer and media buying as much as the edit, so never rank editors by it or present an editor average.

## Inputs

- **Window**: default is the previous calendar month (run on or after the 5th so 7-day click attribution has settled). Accept a custom range ("1–15 November").
- **Editor** (optional): any part of a name. Narrows the tickets and the Foreplay pull to that editor's clients.
- No other filters.

## Step 0 — Find the ticket export

The export always has to be done manually by Tim from Notion; there is no live query step.

1. Use the Filesystem connector (`list_allowed_directories` first) on `D:\Hambi\04. Post Production Lead\Net New Ads Tracking`. Find the newest `EditorTickets_HP-NetNew_Approved_YYYY-MM-DD.csv`. It may sit inside a folder with the same name.
2. If the newest dated folder only holds Notion's default files, the right one is `Tickets <id>_all.csv` (the full database export, several MB). Ignore `Untitled <id>.csv` (a view export, missing Concept # and Type) and the `.md`. Rename the `_all.csv` to the convention with `move_file`, then tell Tim you did.
3. If there's no export, or the newest is more than 7 days older than today, ask Tim for a fresh one: in Notion, Editor Tickets → ••• → Export → CSV, include subpages off. No filters needed; the script filters. Save into the folder as `EditorTickets_HP-NetNew_Approved_<today>.csv`.
4. Copy it to the sandbox with `copy_file_user_to_claude`.

## Step 1 — Prepare tickets

```bash
SK=<this skill's directory>; WD=/home/claude/ept
python $SK/scripts/prepare_tickets.py "<csv>" $WD --to <window end> [--editor "<name>"]
```

- Exit 2: the file is a view export or missing columns. Tell Tim what's missing and stop.
- Exit 3: the editor name is ambiguous or not found. Show the options it printed and ask which one.
- Read the printed summary and `$WD/pull_plan.json`. Clients marked `not_in_clients_json` need adding to `references/clients.json` (find their lens with Foreplay `get_lenses`). Mention them; carry on without them.

## Step 2 — Pull ads from Foreplay

For every client in `pull_plan.json["pull"]`, for every lens in it, call `get_lens_insights`:

- `lens_id`: from the plan; `provider`: `facebook`; `dimension`: `ad_names`; `fields`: `spend,roas`
- `from` / `to`: the window; `sort`: `-spend`; `limit`: 10
- `filters`: `{"ad_name_ct": <lens name_filter>, "spend_gt": 100}`
- Pages: up to 2 per lens on a full run, up to 5 on an editor run. Stop early when `pages` is reached.

After each call, append its rows to `$WD/ads.json` with a short Python snippet (create the file as `[]` first). One object per row:

```json
{"client": "<label from the plan>", "region": "<lens region or empty>", "currency": "<metadata.currency>",
 "ad_name": "<group_by, copied exactly>", "spend": 1234.5, "roas": 0.87}
```

Copy `group_by` verbatim: the script parses CM, concept # and batch from it, and drops iterations, statics and UGC itself. If a lens returns a permission error, note it for the summary and move on. If `spend`/`roas` are rejected as keys, call `get_lens_metrics` once for that lens and use the closest spend and ROAS keys.

## Step 3 — Match and build the workbook

Read `/mnt/skills/public/xlsx/SKILL.md` first, then:

```bash
OUT=/mnt/user-data/outputs/EditPerformance_HP-NetNew_<from>_to_<to>[_<FirstName>].xlsx
python $SK/scripts/match_and_report.py $WD --from <from> --to <to> --out $OUT
python /mnt/skills/public/xlsx/scripts/recalc.py $OUT
```

Fix any formula errors recalc reports, then `present_files`. The Filesystem connector only writes text, so tell Tim to save the download into the Net New Ads Tracking folder.

What the workbook contains, so you can describe it accurately:
- **Read me**: window, data sources, match rule, exclusions, clients not covered and why. On editor runs it opens with the coaching-not-ranking note.
- **Matched concepts**: pod, client, account (for multi-account clients), CM, concept #, concept, ad type, editor(s), shared flag, currency, spend, purchase value, ROAS, and client typical ROAS (formula) for context.
- **Unmatched ads**: by spend, with the reason and, where all candidate tickets share an editor, the likely editor.
- **Approved, no spend found** (editor runs only): their approved tickets due in the 60 days to the window end with no matching ad. Usually not launched yet.

## Step 4 — Summary in chat

Keep it short and blame-neutral:
- Matched concepts, unmatched ad groups and roughly how much spend sits unmatched.
- The 2–3 biggest unmatched items and the one-line fix for each (e.g. "ad name has no CM", "tickets reuse concept numbers").
- Clients not covered (no lens, lost access, client naming).
- One reminder that ROAS compares within a client, and spend is in each account's currency.
Don't list editors by ROAS, don't name a "worst" concept or editor, and don't total spend across currencies.

## Matching rules (what the script does)

- Tickets: Ad Type HP or AI HP, Type = Net new - Editor, Status Approved or Live, client linked. No due-date cutoff: older concepts are often the biggest spenders. Tickets with no client linked belong to churned clients and are ignored.
- Concept # comes from the field, or from the ticket title (`[C4]`, `CONCEPT #7`) when the field is empty.
- An ad matches on client + CM + concept #. If the ad has no CM, or several tickets fit, words from the concept name break the tie. If tickets still tie but share an editor, the editor is reported as "likely". Otherwise the ad stays unmatched with the reason.
- Multi-account clients (Pore Favor US/AU/UK) are kept as separate rows by account.

## Maintaining the skill

- New client, churned client or changed lens: edit `references/clients.json` (key = text that appears in the client name on tickets; `name_filter` = text that HP ads in that account contain).
- If a client changes its ad naming, check a few names against the parser rules at the top of `scripts/match_and_report.py`.
