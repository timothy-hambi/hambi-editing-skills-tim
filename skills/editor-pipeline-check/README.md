# editor-pipeline-check

**Status:** Live

One skill for every status check on Hambi's Editor Tickets board: the scheduled 12AM PH daily run, the morning brief / pre-work update, the deadline or EXT Delivery on-track check, the editor capacity report, and the Notes check with Slack nudge drafts. Use whenever Tim asks for a morning brief, a pre-work update, how we're doing on deadlines, whether an EXT delivery is on track or at risk, who has room for a ticket, an end-of-day capacity report, a full status check, the daily pipeline check, the Notes check or Notes column checklist, or which editors haven't updated their tickets, and whenever the scheduled 12AM PH run fires. It reads Notion through Tim's Notion token (notionApi tools) when available and falls back to the Notion connector with its hourly query allowance, taking one shared snapshot per run either way. Replaces editor-pipeline-status and editor-notes-check.

The instructions Claude follows are in `SKILL.md`.
