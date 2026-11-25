---
name: "iteration-editor"
description: "Edit an iteration of an already-running ad without Premiere: Notion Iteration Ticket (Iterations table, one row per variation) → find the original → change sheet → approval → FFmpeg render with a lock check that proves nothing else moved → review rounds (Edit Review if installed, otherwise chat) → Premiere XML. Use whenever Tim or an editor shares a ticket named Iteration_…, a ticket with Ad Type Iterations, a 'Link to original', or asks to iterate on, tweak, re-hook, re-VO, re-caption, reorder, re-CTA or add an offer/BFCM angle to a finished or live ad, e.g. 'do this iteration', 'iteration-editor', 'make the V1 and V2 iterations', 'swap the hook on the winning ad', 'just the change sheet for this iteration'. Use this instead of hp-editor-agent or premiere-script-prompt when there is no script table and the job is a few changes to an existing edit."
---

# Iteration Editor (native edit)

An iteration takes an ad that is already finished and running, changes a few named things, and ships the result as a new ad. The strategist is testing one idea (a new hook line, a different opening clip, a new CTA), so the test only means something if **nothing else changes**.

That is what makes this different from `hp-editor-agent` and `premiere-script-prompt`. There is no script table to cut from. The brief is a short free-text list of changes, and the job is:

1. Do exactly those changes.
2. Leave everything else frame-for-frame and sample-for-sample as it was.
3. Prove it.

The edit is done in the cloud workspace with FFmpeg and Python. Premiere isn't needed until the XML hand-off.

## Non-negotiables

1. **Only the listed changes.** If something isn't in the row's Description, it stays. Don't tidy, re-grade, re-caption, re-level or "improve" locked sections, even where they break a house standard. Flag those in the change sheet instead and let Tim decide.
2. **Approval gate.** Never render before the user approves a change sheet ("APPROVED vN"). Never export the XML before the edit is signed off.
3. **Locked sections come from the original export.** Rebuild only the section that changes. Everything else is taken straight from the original's final MP4, so it can't drift.
4. **Lock check on every render.** Run `scripts/lock_check.py` and report the result. A failed range blocks delivery.
5. **One source of truth.** All edit decisions live in `spec.json`. The renderer, the lock check and the XML builder all read it.
6. **Ticket wording is exact.** New VO lines, on-screen text and offers are copied character for character from the ticket. If the ticket has a typo or breaks a client rule, flag it and ask. Don't fix it silently and don't paraphrase (standards C7).
7. **Version every round.** `vN` in every filename, and never overwrite a delivered version. Note the two kinds of number: **V1, V2** are the ticket's variations (different ads); **v1, v2** are review rounds of the same variation.

## Reference files

Same set as `hp-editor-agent`. A later file overrides an earlier one, and for **new or changed elements only**:

1. **House standards:** `standards/editing-standards.md` (synced into the Project; local clone `D:\Hambi\03. Claude\hambi-editing-skills-tim\hambi-editing-skills-tim\standards\editing-standards.md`), including its Client overrides appendix.
2. **Client rules:** `brand-hubs/<client>.md` in the repo (lowercase, hyphenated; local clone `D:\Hambi\03. Claude\hambi-editing-skills-tim\hambi-editing-skills-tim\brand-hubs\`) if it exists, otherwise the client's Notion Brand Hub.
3. **The ticket.** What the ticket says wins. Flag any conflict.

If `D:\Hambi\...` isn't reachable, say so in one line and carry on with the Project copy.

## Workflow

### Review mode (decide once, before the preflight)

Renders are reviewed in **Edit Review** when the user has it, and in chat when they don't. Nothing else in the workflow changes between the two.

1. **Edit Review mode** needs all of these:
   - the computer tools `device_list_dir`, `device_stage_files` and `device_commit_files`, plus `SendUserFile`;
   - `review.html` in `D:\Hambi\03. Claude\Edit Review\`. If it isn't there, look for an `Edit Review` folder holding `review.html` in the connected folders (one `device_list_dir` per connected root, no deeper search). Use the folder you find as `<ER>` everywhere below.
2. **Chat mode** is the default whenever any of that is missing: a regular chat, a computer that isn't linked, or someone who doesn't have the review app. Say it in one line ("Edit Review isn't set up here, so I'll post renders in chat") and carry on. Don't stop the job, and don't ask the user to install or move anything.

Record the mode in the preflight table. If the computer drops mid-job, switch to chat mode for that round and say so.

### Resume check (Edit Review mode only)

1. Work out the job code from the message (`iteration-editor: notes done for <CODE> v<N>`, `iteration-editor: APPROVED <CODE> v<N>`) or from the ticket's naming.
2. `device_list_dir` on `<ER>\jobs\<Seq base>\`. If it has `work\spec.json`, the job is in progress:
   - stage `job.json`, `work\spec.json`, `work\original_map.json`, `notes.json` and `status.json`;
   - re-download the original export from the Frame.io or Foreplay source recorded in `spec.json` (or stage `<ER>\jobs\<Seq base>\original\` if it's there);
   - say in one line which version you're resuming from and carry on at step 8 or step 9.
3. Otherwise it's a new job. Never overwrite a saved `spec.json` with a new v1 unless the user asks for a fresh start.

In chat mode there's no resume. A new session starts from step 1, using the change sheet and `spec.json` the user still has in the chat.

### 0. Preflight

One short table, read-only. Any ❌ that blocks the job stops the run.

- **Notion:** fetch the ticket and query the Iterations table.
- **Frame.io:** `mandatory_init` (account `eb4ebb8d-7328-4a67-b3ac-aa654a019fd1`).
- **Foreplay:** `get_lenses` for the client. This only matters when Link to original is a Foreplay link; if the connector is missing, fall back to Frame.io.
- **Review mode:** Edit Review (with the `<ER>` path) or chat, from the check above. Chat mode is never a ❌.
- **Cloud tools:** `ffmpeg -version`; `pip install faster-whisper --break-system-packages`.
- **AI voice:** is a voice connector (e.g. ElevenLabs) connected? Only matters if a row changes VO.

### 1. Read the ticket

Fetch the page with `notion-fetch`. An Iteration Ticket has almost no body. The brief is in two places:

- **Page properties:** Client Name, Campaign (CM#), Concept #, Variations, Angle, Funnel Stage, Persona, Due date, Naming Convention.
- **The inline `Iterations` database.** Take its `collection://` URL from the page and query it with `notion-query-data-sources` in **rows** mode (it keeps links and line breaks). Each row is one variation:

| Column | Use |
|---|---|
| Concept Name | Ends in the variation ID (`- V1`, `- V2`). |
| Description | The change list. This is the brief. |
| Iterating On | Hook, Body or CTA. The section the changes should sit in. |
| Optimisation | TSR, CTR or Hold Rate. What the strategist is trying to move. |
| Link to original | The ad being iterated on (often a Foreplay share link). |
| Hypothesis | Why. Useful for judgement calls; often empty. |

Then:

- **Inherit blanks.** If a row has no Link to original, use the one from a sibling row and say so.
- **Count check.** Rows should equal the Variations property. Flag a mismatch.
- **Scope check.** If a change sits outside the row's Iterating On section (e.g. Iterating On = Hook but a body line changes), flag it. It's usually fine, but it's the first sign of a misread ticket.
- **Break each Description into a change list.** One row per change, typed with the table in step 4. Keep the strategist's wording next to it. Timecodes in tickets are approximate ("0:00 to 0:04"); the real ones come from step 3.
- **Split "change" from "keep".** Lines like "Everything from '…' onwards stays exactly as it is" define the lock. Find that sentence in the transcript and use its first word as the lock boundary.
- If the user was given the editor-side ticket (Editor Tickets database) rather than the client ticket, follow its link back to the client ticket for the Iterations table, and read the editor ticket's Notes too.

### 2. Find the original

You need two things: the **final export** of the original (the base), and **parts** for whatever section changes.

**The final export.** Try in this order:

1. **Foreplay (the live ad).** When Link to original is a Foreplay link, pull the file through the Foreplay connector. Don't ask the user to download it.
   - **Lens share link** (`app.foreplay.co/share/lens-ad/<share_id>`):
     1. `get_lenses` with the client name as the `name` filter. A client can have several lenses (e.g. one per country); check the ones whose name matches.
     2. `list_lens_creative_share_links` for that lens with `limit: 100`, paging until the share link whose `id` equals `<share_id>` turns up. The result can be large and saved to a file; parse it with a short script rather than reading it. The match gives the `ad_id`.
     3. `get_lens_ad` with the `lens_id` and `ad_id`. That returns `video_url` (a direct MP4), `ad_name`, `ad_status`, the ad copy, and `ai_transaction.transcription` with timed segments.
   - **Discovery link** (`app.foreplay.co/discovery?ad=<id>`): `get_ad_by_id`.
   - Download the `video_url` with `curl -sSL` into its own folder (`src/`) and `ffprobe` it.
   - Keep `ad_name`: it's the in-house or Meta name and the best search term for steps 2 and 3.
2. **The original's own ticket.** Search the client's Review Pipeline for the original concept (the name and concept number are usually in `ad_name` or the file name) and open its Frame Link. Download the newest approved version from the version stack.
3. **A Frame.io search** for `ad_name`, lexical.
4. **Ask the user** to drop the MP4 into a connected local folder, and stage it.

**Pick the base.**

- Foreplay gives the file Meta serves, which is often 720×1280 and re-compressed.
- If a Frame.io export is found, compare the two (file size or `md5sum`, then resolution and duration):
  - **Identical bytes:** say so in one line and use either.
  - **Same edit, better quality on Frame.io:** use the Frame.io export.
  - **The content differs** (e.g. a later client round went live): ask which one is live before mapping.
- If Foreplay is the only source, use it, match its size in the render, and note the resolution under Open points.

Record the source (`foreplay: lens_id/ad_id` or `frameio: file_id`) in `spec.json` `original`, so the resume check can download it again.

**Parts.** Only what the changes need. Look in the original ticket's Frame folder and the client's HP library for:

- clean (caption-free, text-free) versions of clips that get re-captioned, reordered or re-voiced;
- the original VO file and the name of the AI voice;
- the music track;
- end cards, offer badges and brand fonts.

Then name the **source tier** for each changed section, because it decides what's possible:

| Tier | You have | What it allows |
|---|---|---|
| **1. Parts** | Clean clips, VO and music for the changed section | A true rebuild of that section. |
| **2. Export + some parts** | The export, plus only some parts | Rebuild what you can; approximate the rest and flag it. |
| **3. Export only** | Just the flattened MP4 | Reorders, trims, new openers, covers and end-card swaps. Burned-in text can only be covered, cropped or replaced. Voice can only be split from music by stem separation. |

If the user says the original **Premiere project** is open on their machine, that beats all three. Offer the project route (see the end of this file).

### 3. Map the original

Build an "original map" so every change has a real address. Save it as `original_map.json` and summarise it in the change sheet.

- **Probe:** codec, fps, size, duration, `color_transfer`, integrated loudness (`ebur128`). The new render matches the original's fps and size.
- **Cuts:** `select='gt(scene,0.2)',showinfo` for the shot list with in/out times.
- **Transcript:** faster-whisper `small.en`, int8, `word_timestamps=True` (load the WAV into a numpy array, as in `hp-editor-agent` step 3). This gives the timing of every VO line and locates the lock boundary.
- **Burned-in text:** a timestamped contact sheet (`fps=2,scale=180:-1,drawtext=%{pts\:hms},tile=10x4`) over the changed section, to see caption style, position and exact on/off times.
- **Audio layers:** is there music under the changed section, and does it run on into the locked section? That decides how the join is handled (step 5).
- **Name the shots** the ticket refers to ("the top down hair parting before and after", "Hannah's before and after") by looking at the frames, and record which shot is which. If two shots could match a description, ask.

### 4. Change sheet (approval gate)

Type each change. These are the common ones; anything else gets a plain description.

| Type | Needs | On an export-only source |
|---|---|---|
| **VO swap** (new line, same voice) | The voice name/ID; the music bed or stem for that section | Stem-separate the section to keep the music, or lay a fresh music section. Flag as approximate. |
| **Captions off / reworded / restyled** | Clean clips for that section | Can only cover or crop. Ask for clean clips first. |
| **Reorder clips** | Nothing if clips are text-free; clean clips if captions sit over them | Works, but burned-in captions travel with their clip. |
| **Clip swap / new opener** | The new clip | Works. |
| **On-screen text / hook overlay** | Brand font; clean clip if replacing existing text | New text works; replacing means covering. |
| **Trim / extend** | — | Trim works. Extending needs more of the source clip, or a slowdown (no freeze-frames). |
| **CTA / end card / offer** | Current end card from the Brand Hub or ticket | Works if the end card is a clean cut-on. |
| **Seasonal banner** (BFCM etc.) | Banner asset, client rule on position | Works as an overlay. This one touches every frame, so the lock check runs on audio only and the sheet says so. |
| **Music swap** | Separate VO, or stems | Stem-separate and flag. |

Write `<Seq base>_ChangeSheet_v<N>.md` to `/mnt/user-data/outputs/<Seq base>/`:

- **Header:** ticket link, client, due date, the original (name, source, duration), source tier, what the strategist is optimising for.
- **Per variation (V1, V2…):**
  - A table: # · Ticket wording · Type · Where in the original (timecode) · What will be done · Source used.
  - **New copy**, exactly as on the ticket: VO lines and any on-screen text.
  - **Timing:** the changed section's old and new length, and the ad's old and new duration. If a new VO line runs longer, the section stretches and everything after it moves later, untouched.
  - **Locked:** the ranges that will be carried over as-is, in original timecode, with the sentence that starts each.
- **Shared across variations:** anything identical in every row, done once.
- **Open points:** missing parts, approximations, ambiguous shot names, anything the ticket doesn't settle.
- **Noticed, not changing:** issues in locked sections (a typo, an old pack shot). Listed for Tim; not acted on.

**Things the ticket often leaves open. Ask, don't assume:**

- The VO changes but the ticket doesn't mention captions. Captions that no longer match the audio break C1, so ask: reword them, or remove them?
- "Use the same AI voice" with no voice named. Look in the original ticket, the client's `brand-hubs/` file and the Notion Brand Hub. If it isn't written down, ask.
- A longer line "so let the clips run slightly longer". Say how: extend each clip from its source if there's footage, otherwise slow it down, and by how much.

**A light sense-check against the Optimisation**, one line each, as advice only:

- **TSR:** the first frame and first second carry it. Say what the new opening frame is and whether it reads with the sound off (H1, H2).
- **Hold Rate:** watch that the change doesn't add dead air or slow the first 5 seconds.
- **CTR:** the CTA and offer must be on screen long enough to read and match the ticket exactly (E2).

**AI voice.** For each new line:

- If a voice connector is available and the voice is known, generate the line. Match the original's pace (words per second from the transcript) and the client's locale (A5). Make two takes if the first sounds off.
- Otherwise put a **VO request** in the change sheet: the exact text per variation, the voice name, the file names to use (`<Seq>_VO.wav`) and where to drop them.
- Never swap in a different voice to keep things moving.

Where the change is visual, render **style frames**: the new opening frame per variation, and one frame per changed text element, `hstack`ed into one JPG. Then ask for "APPROVED vN" or tweaks. Keep the chat summary to a few lines.

**Sheet-only mode.** If the user asks for "just the change sheet" (e.g. to brief an editor who has the original project), stop here and deliver the sheet as the hand-off. It should be complete enough for an editor to action without opening the ticket.

### 5. spec.json

Same shape as `ugc-revision` and `hp-editor-agent`, with the original as a source and a `locked` list per variation:

```json
{
  "client": "CS", "seq_base": "CS_HM_CM5_Iteration_C2", "version": 1,
  "fps": 30, "width": 1080, "height": 1920,
  "original": {"local": "src/original.mp4", "device": "D:\\...\\original.mp4", "duration": 31.2, "lufs": -14.3},
  "sources": {"ba_parting": {"local": "src/ba_parting_clean.mov", "device": "…"}},
  "variations": {
    "V1": {
      "segments": [
        {"src": "ba_parting", "in": 0.0, "out": 1.9},
        {"src": "ba_hannah",  "in": 0.0, "out": 1.8},
        {"src": "ba_curly",   "in": 0.0, "out": 1.8},
        {"src": "original",   "in": 4.07, "out": null}
      ],
      "audio": [
        {"src": "V1_VO", "at": 0.0, "gain_db": -1.2},
        {"src": "music_hook", "at": 0.0, "out": 5.5, "gain_db": -18},
        {"src": "original", "in": 4.07, "out": null, "at": 5.5}
      ],
      "overlays": [],
      "locked": [{"label": "body", "orig_in": 4.07, "orig_out": 31.2, "new_in": 5.5}],
      "changes": [["VO swap", "Hook line replaced, same voice"], ["Captions off", "No captions 0-5.5 s"]],
      "notes": [["Approximation", "Hook music rebuilt from stem separation", 0]]
    }
  }
}
```

Rules:

- **Cut the locked boundary on a frame, at a real cut where possible,** and at a gap between words in the audio. A boundary mid-shot or mid-word shows.
- **Locked audio is not re-processed.** No `loudnorm` over the whole ad, no re-EQ. Level the *new* elements to match the original instead: new VO to the original VO's loudness, new music to the original bed's level under speech.
- **The join.** If music runs across the boundary, the changed section's music has to meet it: use the real track if you have it, otherwise the separated stem, with a short crossfade (2–4 frames) that sits before the locked range starts, never inside it.
- **Length changes ripple.** When a changed section gets longer or shorter, everything after it shifts and `new_in` moves with it. Nothing downstream is re-timed.
- **No freeze-frame holds** (they don't survive XML import). Extend from source or slow the clip.
- New text, captions and cards follow the client rules and the original's own style (font, size, position, box), measured from the original map so the new element looks like it was always there.

### 6. Render

One variation at a time (parallel renders run out of memory).

- **Picture:** `trim` → `setpts` → `fps` per segment, `concat`, as in `ugc-revision` step 5. Tone-map only new HLG sources; the original export is already SDR.
- **Audio:** build from the `audio` list with `adelay`/`amix` (`normalize=0`) or `concat`; original audio passes through at unity gain.
- **Encode once:** x264 `-crf 16 -preset medium`, the original's fps and size, bt709 tags, AAC 256k, `+faststart`.

**QC each variation:**

1. **Lock check.** `python scripts/lock_check.py --original src/original.mp4 --new <file> --spec spec.json --variation V1`. It compares every locked range, picture and sound, and prints PASS or FAIL. Put the table in the change sheet. On a FAIL, fix the cause (an offset, a stray filter, a level change) and re-render; don't deliver around it.
2. **Change check.** For each change in the sheet, look at a frame strip (and listen, for VO) and confirm it's done as written. Check the new VO against the ticket word for word by transcribing it.
3. **The join.** A frame strip two frames either side of every boundary, and a listen across it: no flash frame, no clipped word (P2), no music jump.
4. **Duration** matches the spec within 0.1 s. Overall loudness is within 0.5 LU of the original.
5. **Standards.** Run the `editing-standards.md` pre-export checklist on the changed sections only.

### 7. Deliver each round

Files go in `/mnt/user-data/outputs/<Seq base>/`: one MP4 per variation, the change sheet with the lock-check table, and SRTs only if captions were added or reworded.

#### Edit Review mode

Don't post the MP4s in chat. `<ER>` is the Edit Review folder found in the review-mode check; its layout is in `<ER>\README.md`.

1. **job.json.** On v1, write `<ER>\jobs\<Seq base>\job.json`:
   ```json
   {"code":"<Seq base>","title":"<Brand> · Iteration · <Concept>","client":"<Brand>","ticket":"<Notion URL>",
    "skill":"iteration-editor","deliver":"the Premiere XML and any SRTs, VO and card files",
    "note":"Iteration of <original name>","updated":"<ISO now>",
    "sequences":[
      {"id":"V1","label":"V1 · <Concept Name>","versions":[{"v":1,"file":"v1/<Seq>_v1.mp4","created":"<date>"}]},
      {"id":"ORIGINAL","label":"Original (live ad)","versions":[{"v":1,"file":"original/<original file name>.mp4","created":"<date>"}]}
    ]}
   ```
   - One sequence per variation (`V1`, `V2`…), then `ORIGINAL` last, so reviewers can flip between them. Add `"srt"` to a version only when captions were added or reworded.
   - `skill` and `deliver` make the app's **Notes done** and **Approve** buttons copy an `iteration-editor:` message instead of the HP one. Older copies of `review.html` ignore them and copy `HP-editor-agent: …`. Treat that message the same way when the code matches an iteration job.
   - On later versions, stage the current `job.json` first, append the new version to each variation that changed, bump `updated` and write it back. `ORIGINAL` stays at v1. Never overwrite the user's `notes.json` or `status.json`.
2. **Upload.** `SendUserFile` each MP4 (and SRT) with `display: attach` to get fileUuids, then `device_commit_files` them into `<ER>\jobs\<Seq base>\v<N>\`. Commit the change sheet (with the lock-check table) into the same folder, and `job.json` to the job root (`stagedPath` works for files written with Write). On v1 only, also commit the original export into `<ER>\jobs\<Seq base>\original\`.
3. **Working files.** After every version, commit into `<ER>\jobs\<Seq base>\work\`: `spec.json`, `spec_v<N>.json`, `original_map.json` and the word timings (`asr.json`). These are what the resume check reads.
4. **Message the app.** Append to `agent.json` `messages` (`{at, version, text}`), e.g. "v1 uploaded: V1, 33.5 → 31.8 s, lock check PASS". It shows on the job's status line.
5. **Chat.** Write 3–5 lines: "v<N> is in Edit Review", the job code, what changed per variation, old vs new duration, the lock check result, ⚠️ approximations and open questions. Ask the user to leave timestamped notes, then click **Notes done → revise** or **Approve v<N>** and paste the copied message here.

#### Chat mode (default)

- `SendUserFile` each MP4 with `display: render`, plus the change sheet. If a folder is connected, also commit the MP4s and change sheet into it with `device_commit_files`, beside the original if it lives there, and say where.
- Use the same 3–5 line summary, and ask for notes as replies in chat, with a timecode and the variation (e.g. "V1 0:09.4: start the bag shot later"). "Approved" or "APPROVED v<N>" in chat signs it off.

### 8. Feedback rounds

**Trigger.** In Edit Review mode, the message the app copies (`iteration-editor: notes done for <CODE> v<N>`, or the older `HP-editor-agent: …` wording for an iteration job code), or the user saying the notes are in. In chat mode, the user's notes in chat.

**Edit Review mode:**

- If `spec.json` isn't in the workspace, run the resume check first.
- Stage `notes.json` and `status.json` fresh. Act on every note with `state` `open` on the latest version. Notes carry `seq` (`V1`, `V2`, `ORIGINAL`), `version`, `t` (seconds into that cut) and `text`.
- If `status.json` isn't `notes_submitted` for the latest version, check before revising, because they may still be adding notes.
- Map each `t` through that variation's `segments` to the original timecode. That tells you whether the note lands in a changed section or a locked one.
- A note on `ORIGINAL` is context, not a change. Reply that it's on the live ad and ask whether it should apply to the variations.
- Reply to every note in `agent.json`: `notes[<id>] = {state: "done" | "dismissed", reply: "<one line>", version: <N+1>, at: <ISO>}`. Use `dismissed` only with a reason. Commit `agent.json` together with the v<N+1> files.

**Chat mode:** answer each note in a numbered list in the same reply as v<N+1>, with the same done/dismissed-with-reason rule.

**Both modes:** each note becomes a `spec.json` change, the version goes up, and only the variations that changed are re-rendered. Run the step 6 QC again, then deliver as in step 7.

Two things are specific to iterations:

- **A note on a locked section** asks for something the ticket didn't. Don't just do it. Reply that it's outside the iteration and ask Tim whether to widen the scope. If he says yes, add it to the change list and shrink the locked range.
- **A note that applies to every variation** (they share a body) is applied to all of them. Say so.

After each round, sort the notes as the other skills do: all clients → offer `editing-standards.md`; this client → offer `brand-hubs/<client>.md`; this ad → stays on the ticket. Don't write any of these without an OK.

### 9. Approval → Premiere XML

**Sign-off** is any of: the app's copied `iteration-editor: APPROVED <CODE> v<N>` (or the older `HP-editor-agent: APPROVED …` for an iteration job code); `status.json` showing `{state: "approved", version: N}`; or "approved" in chat. In Edit Review mode, stage `status.json` first and check that the approved version is the latest. If notes are still open, list them and ask whether to ignore them.

On sign-off, build **one** FCP7 xmeml v4 file, `<Seq base>_ALL_v<N>.xml`, with one sequence per variation, following `ugc-revision` step 8 for structure, `pathurl`s and validation.

- **V1:** the original export for the locked ranges, and the new clips for the changed section.
- **V2:** card and text PNGs.
- **A1:** original audio for the locked ranges. **A2:** new VO. **A3:** new music.
- **Markers:** one at each locked boundary ("Locked from here: original export"), one per change, and one per approximation.

Tell the user what the XML is: the locked sections are the flattened original, not its layers. If the editor has the original Premiere project, the faster hand-off is often the **changed section only** dropped into a duplicate of the original sequence. Offer that, and say which markers to line it up on.

Validate the XML: it parses, ids are unique, each file is defined once, and there's one sequence per variation.

**Deliver:**

- **Edit Review mode:** `SendUserFile` (`attach`), then `device_commit_files` the XML, any SRTs, the new VO files and card PNGs (in `cards\`) into `<ER>\delivery\<CODE>\`. Point the `pathurl`s there. Append an `agent.json` message: "Approved v<N> delivered: XML in delivery\<CODE>".
- **Chat mode:** `SendUserFile` (`attach`) each file. If a folder is connected, also commit them into a `<Seq base>_delivery\` subfolder there and point the `pathurl`s at it. If nothing is connected, the `pathurl`s can't be known: put the original export, VO and cards beside the XML, say they need relinking on import, and add a frame-0 marker saying so.

## Naming

- Use the ticket's **Naming Convention** property if it resolves.
- Otherwise: `[Brand]_HM_CM[#]_Iteration_C[#]_V[n]`, e.g. `CS_HM_CM5_Iteration_C2_V1`. Multi-word brands use their initials. `<Seq base>` is the same without `_V[n]`.
- MP4: `<Seq>_v<N>.mp4` · Change sheet: `<Seq base>_ChangeSheet_v<N>.md` · XML: `<Seq base>_ALL_v<N>.xml` · VO: `<Seq>_VO.wav`.

## Project route (only when the user offers it)

If the original Premiere project is open and the Premiere connector is live, the cleanest iteration is made there: duplicate the original sequence once per variation, name the copies with the convention above, and make only the listed changes in each copy. Steps 1–4 are the same and the approval gate still applies. Use the connector preflight and build rules in `premiere-script-prompt/SKILL.md`. Export a review MP4 per variation and still run the lock check against the original export.

## Known limits (say these up front when they apply)

- Burned-in captions and text can't be removed from a flattened export. They need clean clips, a cover, or a crop.
- Replacing VO over music on a flattened export relies on stem separation (`pip install demucs --break-system-packages`, `--two-stems=vocals`, run in the background). It's usually clean enough under a new VO but can leave artefacts. Always flag it and offer the alternative of a supplied music track.
- Foreplay's file is the one Meta serves, often 720p and re-compressed. If no better master turns up, the iteration is delivered at that size, and the sheet says so.
- The same AI voice needs the voice's name or ID. A close match isn't the same voice.
- A full-frame change (banner, resize, re-grade) means there is no locked picture to check; say that the lock check covered audio only.
- The XML carries the flattened original for locked sections, not the original's layers.

## Pitfalls

- Reading the ticket page alone and missing the Iterations table. The page body is nearly empty; the brief is in the database rows.
- Treating V2 as a revision of V1. They are separate ads from the same original, each built from the original, not from each other.
- Normalising the whole render to −14 LUFS. That changes the locked audio. Match new elements to the original.
- Fixing things nobody asked for. An iteration with an extra change is a broken test.
- Everything in `hp-editor-agent`'s Pitfalls about Frame.io listings, `stagedPath` commits, background transcodes and reading Edit Review files fresh applies here too.
- Stopping the job because Edit Review isn't there. Chat mode is the normal path for anyone without the review app.
- Writing `job.json` without `"skill":"iteration-editor"`. The app then copies an `HP-editor-agent:` message, which can start the wrong skill in a fresh chat.