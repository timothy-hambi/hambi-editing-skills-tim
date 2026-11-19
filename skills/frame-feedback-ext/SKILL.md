---
name: "frame-feedback-ext"
description: "EXT: collect client Frame.io feedback on HP edits for named active client projects (P#) over the last 30 days and turn it into Brand Hub / client-override updates."
---

# EXT — Client Frame Feedback Sweep (HP only)

This skill runs when Tim's prompt starts with **EXT** followed by one or more projects, for example `EXT P8 - Bella+Duke` or `EXT P13 Revive Collagen 2026, P2 NB1`.

It reads only the projects Tim names. Never widen the scope to other projects.

## Scope rules

- **Projects:** only the ones named in the prompt. Each must be **active** and its name must start with `P<number>`.
  - If a named project is inactive or doesn't start with P#, say so in one line and skip it.
  - If the name is ambiguous, list the matches and ask which one to use.
- **Window:** the last 30 days by default. Use a different window if Tim gives one.
- **Folders:** client review folders only. The default name is `EXT`; some projects use `External` instead. Variants such as `EXT - ROUND n` count. Keep only the ones updated inside the window.
  - **No EXT/External folder found:** don't guess or use other folders. Flag the project in the chat reply and in the report's Gaps list as "No EXT/External folder — chase AM". Then carry on with the other projects.
- **Within those:** HP folders only (`HP`, `HPs`, `High Prod`, `HP_*`), including their subfolders. Ignore UGC, Design, Statics and Iterations folders.

## Steps

1. **Set up Frame.io.** Call `mandatory_init` with `include_accounts=false`. The account is `eb4ebb8d-7328-4a67-b3ac-aa654a019fd1`. Don't use `read_audit_logs`; it errors on this account.
2. **Find the project.** Use `read_context` with `include=["projects"]` and page through until the named project is found. Check it's active and note its `root_folder_id`.
3. **Find EXT folders.** Run `search_assets` scoped to the project (folders only), once with query `EXT` and once with `External`. Only keep folders whose name starts with EXT or External; ignore partial matches such as "Extras" or "Texture". Keep the ones updated inside the window.
4. **Find HP folders.** Run `list_folder_children` (sort `updated_at_desc`) and follow the HP folders down.
5. **Read comments.** For every file or version stack updated inside the window:
   - Run `list_version_stack_versions` and read comments on every version, including replies.
   - Keep comments created inside the window.
   - Skip acknowledgements.
   - Store each comment as JSONL in the scratchpad with these fields: project, folder path, file, version, timecode, author, created_at, text, is_reply, completed.
6. **Separate client from Hambi.** Client comments often have no owner (`owner: null`) or a client email address. Replies from Hambi logins ("Hambi Team", am.strat@…) are our responses. Keep them as context, but don't count them as client feedback.
7. **Keep it in one context.** Don't spawn agents for one or two projects. If a project has more than about 40 HP files in the window, give Tim the count and offer either to cap at the latest 40 or to fan out.

## Analysis

Sort every client comment into one bucket:

- **Brand rule** — standing preferences: fonts, colours, tone, offer wording, pronunciation, banned visuals, compliance limits, how pets and talent may be shown. These go to the Brand Hub and the Client overrides.
- **Taste pattern** — things the client keeps choosing, such as preferred music mood, pacing, B-roll style or caption density. These go to the Brand Hub as "client preferences".
- **Ad-specific** — count these, but don't turn them into rules.
- **Should have been caught internally** — typos, captions covering the product, wrong CTA, old packaging. These are internal QA misses, so map each to its `editing-standards.md` rule ID.

Also note:

- **Revision load:** how many rounds each HP needed, and the average number of client comments per HP.
- **Escalation signals:** comments that override a signed-off brief, mention compliance, or say "for the future" or "we did outline". These need an AM/CS heads-up.

## Output

Create a living Claude Doc titled `EXT Feedback — <Project(s)> — <date range>`. Follow the docs skill: open the doc with an outline first, then fill it section by section. Sections:

1. **Overview** — the projects, the window, how many HP files and client comments were read, and the number of revision rounds.
   - **Gaps:** projects with no EXT/External folder, no HP folder, or no client comments in the window. Each gets a "chase AM" checkbox.
2. **Top themes** — a bar chart of client comment counts per theme, with one sentence of reading.
3. **Brand rules to add** — a table for each client of rule → source comment (short quote and date). This feeds the Brand Hub directly.
4. **Client preferences** — the taste patterns, with how often each came up.
5. **Internal QA misses** — client notes we should have caught, with the standards rule ID and the count. This is the strongest signal for team training.
6. **Escalations** — anything the AM or CS should know.
7. **Next steps** — checkboxes: update the Brand Hub, update the `editing-standards.md` Client overrides, cover the QA misses in team training or QA, and send escalations to the AM/CS.

Get Tim's approval before writing to any Brand Hub page in Notion or to `editing-standards.md`. Once he approves:

- update the Client overrides table in `editing-standards.md` (the Project doc and `D:\Hambi\03. Claude\SKILLS\editing-standards.md`), with a changelog line;
- offer to draft the Brand Hub additions on the client's Notion Brand Hub page.

Keep the chat reply to one line plus the doc link. If any project had no EXT/External folder, list it on a second line, e.g. "No EXT folder: P4 - Nuovva — chase AM".

## Rules

- Read only. Never create, edit, resolve or delete anything in Frame.io.
- Never post client feedback outside the doc.
- Keep everything blame-neutral, and present client notes as preferences, not complaints.
- Quote as briefly as possible.