# Hambi Editing Skills

The single home for the Editing department's standards, Claude skills, SOPs, Brand Hubs and training material.

**Owner:** Tim Tamon (Post Production Lead, Systems)
**Escalation:** Sam Lloyd (Post Production Manager)

If a file here and a copy somewhere else disagree, the version in this repo wins.

---

## What's in here

| Folder | What it holds |
|---|---|
| `standards/` | House editing standards that apply to every HP edit. Every editing skill reads these first. |
| `skills/` | Claude skills for repeatable work, with one folder per skill. |
| `sops/` | Finished SOPs for the Editing team, in Notion SOP format. |
| `brand-hubs/` | One file per client: fonts, colours, CTAs, offers, pronunciation, banned visuals. |
| `training/` | The fortnightly training plan and a log of every session. |

## Order of authority

When rules conflict on an edit, follow the highest source and note the conflict in the handoff:

1. The ticket
2. The client's Brand Hub (`brand-hubs/`)
3. The house standards (`standards/editing-standards.md`)

## Where a new rule goes

- **It applies to every client.** Add it to `standards/editing-standards.md` as a numbered rule and add a changelog line.
- **It applies to one client only.** Add it to that client's file in `brand-hubs/`.
- **It applies to one ad only.** Log it on the Notion ticket. It doesn't go in this repo.
- **You're not sure.** Raise it with Tim before adding it.

## How to make a change

1. Open the file and click the pencil icon.
2. Make the edit.
3. Write a commit message that says what changed and why, then click **Commit changes**.

Good commit messages:

- `Standards: add P9 (don't cut mid-breath)`
- `Brand Hub: Naydaya new 15% offer stamp`
- `Acting PPM: add BFCM allocation rule`
- `Training: log session 04 (Frame tagging)`

To see what changed and when, open any file and click **History**.

## Using this repo with Claude

The repo is connected to the Claude Project "Post Production Lead — Systems & Acting PPM". After you commit changes here, click **Sync now** in the Project's GitHub source so Claude reads the latest version.

Claude can read this repo but can't edit it. All changes are committed here by a person.

## Naming conventions

- Use lowercase with hyphens: `revive-collagen.md`, not `Revive Collagen.md`.
- Every skill folder has a `SKILL.md`, which holds the instructions Claude follows.
- Training sessions are named `YYYY-MM-DD-topic.md`, for example `2026-11-24-frame-tagging.md`.
