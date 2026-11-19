# Skills

One folder per Claude skill. Each folder contains:

- `SKILL.md`, the instructions Claude follows (required)
- `README.md`, a plain-English summary for the team: what it does and when to use it
- any `references/` or `scripts/` the skill needs

| Skill | Status | Purpose |
|---|---|---|
| `ppm-overview/` | Live | Acting PPM: allocation app overview, INT/EXT dates, capacity, next month's allocation |
| `editor-pipeline-check/` | Live | Daily 12AM PH run, morning brief, deadline and capacity checks, Notes check |
| `ticket-status-checker/` | Live | Checks which Client Review tickets are actually approved (read-only) |
| `slack-checkmark-check/` | Live | Who has and hasn't ✅'d a Slack message |
| `premiere-script-prompt/` | Live | Ticket to timecoded cut sheet, then build in Premiere after approval |
| `hp-editor-agent/` | Live | HP/UGC rough cut without Premiere (Cowork) |
| `iteration-editor/` | Live | Iterations of running ads with a lock check |
| `ugc-revision/` | Live | Actions Frame.io feedback on creator UGC ads |
| `frame-feedback-int/` | Live | Internal Frame.io feedback sweep into editing standards updates |
| `frame-feedback-ext/` | Live | Client Frame.io feedback sweep into Brand Hub updates |
| `edit-performance-tracker/` | Live | Monthly report on how HP edits perform once live |
| `qa-feedback-composer/` | Planned | Turns QA notes into Kind Candour feedback for Tim's pods |
| `sop-pipeline/` | Planned | Drafts SOPs in Notion SOP format |
| `training-planner/` | Planned | Plans and logs the fortnightly training sessions |
| `brand-hub-builder/` | Planned | Builds Brand Hubs and the Frame.io tagging structure |

Update the status column when a skill moves from Planned to In progress to Live.
