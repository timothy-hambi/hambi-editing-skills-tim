---
name: "frame-feedback-int"
description: "INT: collect internal Frame.io feedback on HP edits for named active client projects (P#) over the last 30 days and turn it into editing-standards updates."
---

# INT — Internal Frame Feedback Sweep (HP only)

This skill runs when Tim's prompt starts with **INT** followed by one or more projects, for example `INT P3 - The Diamond Store` or `INT P6 Cornish Seaweed, P7 Hunter & Gather`.

It reads only the projects Tim names. Never widen the scope to other projects.

## Scope rules

- **Projects:** only the ones named in the prompt. Each must be **active** and its name must start with `P<number>` (e.g. `P3 - The Diamond Store`).
  - If a named project is inactive or doesn't start with P#, say so in one line and skip it.
  - If the name is ambiguous (e.g. two `P4 - Omni` projects), list the matches and ask which one to use.
- **Window:** the last 30 days by default (comments with `created_at` on or after today minus 30). Use a different window if Tim gives one.
- **Folders:** internal review folders only. The default name is `INT`; some projects use `Internal` instead. Variants such as `INT - ROUND n` count. Keep only the ones updated inside the window, and skip anything marked "Do not use" unless Tim says otherwise.
  - **No INT/Internal folder found:** don't guess or use other folders. Flag the project in the chat reply and in the report's Gaps list as "No INT/Internal folder — chase AM". Then carry on with the other projects.
- **Within those:** HP folders only (`HP`, `HPs`, `High Prod`, `HP_*`), including their subfolders. Ignore UGC, Design, Statics and Iterations folders.

## Steps

1. **Set up Frame.io.** Call `mandatory_init` with `include_accounts=false`. The account is `eb4ebb8d-7328-4a67-b3ac-aa654a019fd1`. Don't use `read_audit_logs`; it errors on this account.
2. **Find the project.** Use `read_context` with `include=["projects"]` and page through until the named project is found. Check its `status` is active and note its `root_folder_id`.
3. **Find INT folders.** Run `search_assets` scoped to the project with `include_files=false` and `include_projects=false`, once with query `INT` and once with `Internal`. Only keep folders whose name starts with INT or Internal; ignore partial matches such as "Interview" or "Intro". Keep the ones updated inside the window.
4. **Find HP folders.** In each kept folder, run `list_folder_children` (sort `updated_at_desc`) and follow the HP folders down.
5. **Read comments.** For every file or version stack updated inside the window:
   - Run `list_version_stack_versions`. Feedback usually sits on **earlier** versions, so read comments on every version.
   - Use `read_comments` with `page_size=100`, include replies, and page with `next_cursor`.
   - Keep comments created inside the window.
   - Skip pure acknowledgements ("done", "thanks", emoji-only) and bare "same as previous" notes.
   - Store each comment as JSONL in the scratchpad with these fields: project, folder path, file, version, timecode, author, created_at, text, is_reply, completed.
6. **Work out who said it.** Most comments come from shared logins ("Hambi Team", "Editors At Hambi"). Use the name signed in the text where there is one ("- Zia", "Saskia:"); otherwise leave the author as the login.
7. **Keep it in one context.** Read Frame.io directly; don't spawn agents for one or two projects. If a project has more than about 40 HP files in the window, tell Tim the count and offer either to cap at the latest 40 or to fan out.

## Analysis

Sort every comment into **one** of three buckets:

- **General** — applies across clients (e.g. "don't cut mid-sentence", "captions cover the product"). These are candidates for `editing-standards.md`.
- **Client-specific** — brand fonts, colours, offers, pronunciation, banned visuals. These go to the Brand Hub and the Client overrides.
- **Ad-specific** — swap this clip, change this word. Count these, but don't turn them into rules.

Tag every General comment with the standards section it falls under: Captions (C/S), B-roll (B), Pacing (P), Hooks (H), Grade (G), Audio (A), CTA (E) or Compliance (K). Count the comments per theme.

Compare the findings against the current `editing-standards.md` (repo file `standards/editing-standards.md`, synced into the Project). Mark each finding as:

- **Already covered** — recurring breaches show a training or QA gap, not a missing rule.
- **New rule** — propose wording.
- **Conflicts with the standards** — flag it.

## Output

Create a living Claude Doc titled `INT Feedback — <Project(s)> — <date range>`. Follow the docs skill: open the doc with an outline first, then fill it section by section. Sections:

1. **Overview** — the projects, the window, and how many HP files and comments were read.
   - **Gaps:** projects with no INT/Internal folder, no HP folder, or no comments in the window, plus deleted files and versions that couldn't be read. Each missing-folder project gets a "chase AM" checkbox.
2. **Top themes** — a bar chart of comment counts per theme, with one sentence of reading.
3. **Repeat issues** — the rules editors keep breaking. For each: the rule ID, how often it came up, and 1–2 short example quotes.
4. **Proposed standards updates** — new or changed rules, worded the way the standards file words them.
5. **Client overrides** — a table of client → rules to add to the Brand Hub.
6. **Next steps** — checkboxes: approve the standards changes, update the Brand Hub, cover the repeat issues in team training or QA.

**Don't edit `editing-standards.md` without Tim's approval.** Once he approves, update the repo file `standards/editing-standards.md` (synced into the Project; local clone `D:\Hambi\03. Claude\hambi-editing-skills-tim\hambi-editing-skills-tim\standards\editing-standards.md`), bump `version` and `updated`, and add a changelog line. Then give Tim a suggested commit message so he can commit and push in GitHub Desktop, then click Sync now in the Project.

Keep the chat reply to one line plus the doc link. If any project had no INT/Internal folder, list it on a second line, e.g. "No INT folder: P4 - Nuovva — chase AM".

## Rules

- Read only. Never create, edit, resolve or delete anything in Frame.io.
- Keep the report blame-neutral. Report patterns; never single out an editor.
- Quote comments as briefly as possible, and only where a quote proves the point.