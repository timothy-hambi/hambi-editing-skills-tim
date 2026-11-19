---
name: "premiere-script-prompt"
description: "Turns a Notion editor ticket (script table, hook variations, Frame.io shot links) plus footage transcripts into a timecoded script prompt (cut sheet) for Adobe Premiere Pro via the Premiere MCP, with SRT subtitles and placeholders, then builds it in Premiere only after the user approves that exact version. Script mode: use whenever Tim or an editor shares a Notion ticket, Frame.io links, footage, a transcript or a VO script and wants an initial cut, rough cut, selects, stringout, paper edit, hook variations, an A-roll/B-roll ad, a founder or interview Q&A or an AI-VO mash-up, e.g. \"turn this ticket into a script prompt\", \"cut this\", \"build the edit\"; also for revising, re-approving, adding B-roll, placeholders or subtitles, or running a connector preflight. Execute mode: use when a new chat starts with \"APPROVED vN. Execute from [path to a ScriptPrompt .md]\" to build an approved sheet in Premiere."
---

# Premiere Script Prompt

Turn a brief (usually a Notion editor ticket) + footage transcripts into a **script prompt**: a versioned, timecoded cut sheet that says, line by line, which words are heard, which take they come from, what covers them, and where they land on each timeline. The script prompt is the contract. Premiere is only touched after the user approves it.

## Two modes, two chats

The skill runs in two separate chats to keep usage down. Script mode carries all the heavy context (ticket, transcripts, audio analysis), and execute mode doesn't need any of it.

| | **Script mode** (chat 1) | **Execute mode** (chat 2, a fresh chat) |
|---|---|---|
| Starts with | A ticket, footage or transcript, e.g. "/premiere-script-prompt Here's the editor ticket…" | `APPROVED v<N>. Execute from <full path to …_ScriptPrompt_v<N>.md>. Skip preflight.` |
| Does | Preflight → ticket → transcripts → takes → tighten → sheet → subtitle and placeholder SRTs → Notion + `Script Prompts\` | Reads the sheet's **Execution data** → builds in Premiere → imports the ready-made SRTs → verifies → closes out |
| Doesn't | Touch the Premiere project | Run the preflight, pull transcripts, open Frame.io or re-read the ticket |
| Steps | 0–8, then 7b (hand-off) | 9 only |
| Model | Any | Sonnet is enough; keep tool results small |

**Decide the mode from the first message.** A message that says "Execute from" plus a `.md` path, or an "APPROVED v<N>" with a sheet path in a chat that has no sheet yet, is execute mode: go straight to step 9. Everything else is script mode.

**Script mode always ends with the hand-off reminder (step 7b).** Every version delivered, and every approval given in the script chat, ends with the reminder to start a new chat and the ready-to-paste execute prompt. Don't build in the script chat unless the user explicitly says to build there (e.g. "build it here", "execute in this chat").

## The approval gate (read first)

Editing someone's project is hard to undo cleanly, and a wrong cut wastes an editor's time more than a slow one. So the work is split in two:

1. **Plan phase (read-only).** Read the ticket, pull transcripts, inspect the project, draft and revise the script prompt. Premiere MCP tools allowed: `ping`, `get_*`, `list_*`, `search_*`, `inspect_*`, `analyze_*`, `detect_*`, `plan_*`, `rank_*`, `create_editorial_context_pack`, `create_context_edit_plan`, `create_editorial_plan`, `preview_*`, `export_frame`/`capture_frame` for reference stills. Writing the script prompt to Notion and to a .md file, and writing the subtitle and placeholder SRT files into the edit folder (`Graphics\Subtitles`, `Graphics\Placeholders`), are part of this phase: they're files on disk, not changes to the Premiere project, and nothing is imported until execute mode.
2. **Execute phase.** Anything that changes the project, timeline, bins or media (`create_*` sequence/subclip/bin, `add_*`, `insert_*`, `overwrite_*`, `apply_*`, `trim_*`, `razor_*`, `ripple_delete`, `remove_*`, `set_*`, `move_*`, `import_*`, `manage_project_context` capture/enrich, `save_project`, exports) runs **only** after the user approves the current version.

What counts as approval: a clear go-ahead naming or plainly referring to the version on screen, e.g. "APPROVED v2", "approved", "go", "execute", "cut it". Anything else is not approval: questions, partial feedback, "looks good but…", silence, answers to the open questions, or approval of an older version.

- **Approval given in the script chat:** mark the sheet `APPROVED v<N>` (Notion title + .md header), then give the hand-off reminder (step 7b) instead of building. Build in the script chat only if the user explicitly asks to.
- If the user approves *and* dictates exact mechanical changes (e.g. "approved, but row 4 out = 13:12:49:20"), apply them, bump the version, regenerate the affected SRTs, show the changed rows, mark it approved and hand off.
- If the change needs your judgement (another take, re-ordering, tightening, "make it punchier"), issue the revised version and wait for approval again.
- Every change after approval creates a new version that needs its own approval. Never execute an unapproved version, even if the user seems in a hurry. "Ready to execute v3 on your approval" costs one message; an unwanted edit costs much more.

## Workflow

### 0. Preflight (always first, before reading the ticket)

**Script mode only.** Execute mode skips this table (see step 9.0). Run this check as the very first action of every new script-prompt thread, before fetching the ticket or drafting anything. A missing connector found halfway through a build means a second thread; found in the first reply, it can usually be fixed in the same chat. Every probe is read-only.

| # | Check | Probe | Needed for | If it fails, tell the user |
|---|---|---|---|---|
| 1 | Premiere MCP (CEP bridge) | `ping`, then `get_project_info` | Everything | Open Window › Extensions › MCP Bridge in Premiere |
| 2 | Premiere UXP bridge | `get_clip_transcript_uxp` on any one source clip ("not transcribed" still counts as connected; "UXP bridge is not connected" is a fail) | Premiere transcripts, marker GUIDs | Open the UXP bridge panel in Premiere |
| 3 | Claude in Chrome + Frame.io | `list_connected_browsers`, then open one shot link from the ticket and confirm it isn't a sign-in page | Shot-link comments, Frame.io transcripts | Connect the Claude in Chrome extension and sign in to Frame.io in that browser |
| 4 | Local file access (edit folder) | A local file/shell tool lists the edit folder and creates then removes a test folder (e.g. `Script Prompts/_preflight`) | Creating `Graphics/Placeholders/`, `Graphics/Subtitles/`, `Script Prompts/`; saving the .md into the edit folder | Enable the local file/shell connector in the Claude desktop app **before starting the chat** (connectors added mid-thread may not load) |
| 5 | Notion | `notion-fetch` the ticket | Reading the ticket, writing the script-prompt sub-page | Reconnect Notion |
| 6 | ffmpeg (local) | `detect_silence` on one source clip | Pause tightening | Restart the Claude desktop app, or `winget install Gyan.FFmpeg` |

Report the result as one short table (✅ / ❌ / ⚠️ per row, one line of fix each) and nothing else. Then:

- **All required rows ✅** → carry on to step 1 in the same reply.
- **Any ❌ on rows 1, 3 or 5** → stop and wait. These block the work. When the user says "re-check", run only the failed probes again.
- **❌ on row 2** → carry on only if Frame.io (row 3) works as the transcript source, and say so. Recheck before execution.
- **❌ on row 4** → ask once whether to continue without it. If yes, the Premiere MCP can still write SRTs, but only into folders that already exist (`build_caption_artifact` with `output_path`), so files land in the edit-folder root and the .md is delivered in chat for the user to file. Record this as a deviation in the sheet.
- **⚠️ on row 6** (ffmpeg works but finds no silence on loud footage) → note it; tighten from word timings and flag cuts to check by ear.

Never treat a connector as available because it worked in a previous thread; probe it in this one.

### 1. Read the brief

**Notion editor ticket (the usual input).** Fetch the page with `notion-fetch`, plus any inline databases (hook variations) with `notion-query-data-sources` (rows mode), and any images on the page (they're often client feedback screenshots; download and read them). In a Hambi ticket:

- **Which script is live:** the ticket often has a planned *Production Script Breakdown* and a later *Editor Ticket* section. If a callout says the script changed on the day (or the Editor Ticket has its own script table), the Editor Ticket wins. Say which one you used in the header.
- **Script table** columns usually include Framework Section, Script Breakdown (for Q&A formats, `Q:` is the question card and `A:` the answer), Visual Description, Text on screen, and **Shot Link** (a Frame.io link per row).
- **Hook variations database:** Variation (Hook 1, Hook 2, …), Script, Shot description, Shot Type, Shot Link.
- **Editor notes / client notes:** footage folder links and standing client rules (e.g. "founder name on the first frame", "before/afters within the first 2 seconds"). Turn these into a "Client standing notes" block and apply them to every relevant row. Flag where the ticket conflicts with one.
- Properties worth carrying: concept name, Ad Type, Campaign, Concept #, due date, number of variations, format/aspect ratio if stated.

**Other inputs** work the same way once you have lines and footage: a pasted script, a VO script (Mode B), or bare footage plus a brief.

Then choose the mode (ask only if it isn't clear):

| Mode | Footage | Who picks the picture |
|---|---|---|
| **A. Dialogue cut** | Founder/interview/UGC/talking head with sync sound, optionally plus B-roll | You pick takes from the transcript, guided by the ticket's shot links; user approves |
| **B. VO mash-up** | AI or recorded voiceover + supplied footage | **User** assigns footage and source timecode per VO line; you prepare, validate and build |

### 2. Transcripts and take references

Every row needs word-level timings, plus a reference for which take to use. Use the first transcript source available:

1. **Premiere's own transcript (preferred).** If the clips have been transcribed in Premiere (Text panel), read them directly. Run `has_transcript_uxp` per source clip (`project_item_id`), then `get_clip_transcript_uxp`. It returns Premiere's native transcript JSON plus a `transcript_revision` (`sha256:…`). Inspect the JSON's structure on first use (segments with word-level start/duration); its times are clip-relative, and word **starts run 0.1–0.3 s early**, so heads and tails come from the audio (step 3b), never from the transcript alone. UXP tools use their own project item IDs, not CEP node IDs: match clips between the two by clip name. This is the fastest route: no browser, no Frame.io sign-in, and the revision hash unlocks Premiere's own analysis tools (`detect_repeated_takes`, `analyze_dialogue_edit_candidates`, `plan_filler_word_removal`) with a genuine revision.
   - These tools need Premiere's **UXP bridge panel** open, alongside the regular MCP Bridge (Premiere 25.6+). If a call returns "Premiere UXP bridge is not connected", ask the user once to open it, or carry on with the next source.
   - If only some clips are transcribed, use Premiere for those and fill the rest from the next source. If none are, say so; the user can batch-transcribe in Premiere (select clips → Transcribe) for next time.
   - Premiere transcripts don't contain the strategist's "best take" marks, so still read the Frame.io comments when the ticket has shot links (see below). Comments alone are quick: just `GetCommentsByAsset`, no transcript download.
2. **Frame.io shot links (fallback for transcripts; main source of take references).** Each link looks like `next.frame.io/project/<project>/view/<assetId>?c=<commentId>`. The comment is the strategist's reference for the preferred take. Sometimes it's an accurate in/out range, sometimes a loose range, sometimes just a start point. Treat it as "which take", and let the transcript decide the exact frames. Use the recipe in "Frame.io extraction" below, **one or two assets at a time** (batch grabs of many assets can freeze the tab), to get, per asset: file name, fps, start timecode, duration, comments (start + duration) and, when Premiere has no transcript, the word-level transcript. The user must be signed in to Frame.io in the built-in browser. If the page lands on a sign-in screen, ask them to sign in (show the browser pane first) and continue.
3. **Supplied transcript file**: SRT/VTT/timestamped TXT/Whisper JSON. Parse with the helper.
4. **Local transcription**: Whisper on the user's machine (`device_bash`, `faster-whisper` with word timestamps), or stage the extracted audio to the cloud workspace if it can't run there.
5. **Mode B VO text only**: estimate ~2.6 words/s and mark every VO timecode `EST`.

Say in the sheet header which source each clip's transcript came from.

Transcripts mishear brand and technical words ("Pore Favor" → "fourth of all", "oil glands" → "oral glands"). Write the *Line (heard)* column with the correct words, and note the mishearing once so nobody "fixes" the cut.

### 3. Pick takes and cut points (Mode A)

For each script row:

- **Find the take.** Start from the Frame.io comment range. If there's no comment, or the comment is only a start point, find the take whose words best match the scripted line, preferring the last complete clean take. Where several takes exist, list the others under "Alternates" with their timecodes.
- **In point:** 3 frames before the first word of the line, but never inside the previous word. Trim slate and pre-roll talk ("three, two, one, action", "okay, so") unless it serves the edit (e.g. "Final question." before the last Q). If the slate ends ≤2 frames before the first word, cut on the first word and flag it ⚠️ to check by ear.
- **Out point:** ~5 frames after the last word ends, never into the next word or crew chatter.
- **Q&A formats:** if the founder speaks the question, keep it unless the user says the text card replaces it, and flag that cutting spoken questions is an easy runtime saving.
- **Ad-libs:** when what was said differs from the ticket's script, use what was said, and note material differences (new claims, dropped lines).
- Snap source in/outs to whole **source** frames. When source and sequence rates differ (25 fps footage in a 23.976 timeline), each segment's timeline length is floor(out ÷ T) − floor(in ÷ T) frames (T = sequence frame duration), which is how Premiere conforms it. Lay out timeline positions in whole sequence frames from those, and put them in the Execution data as start_frame / frames.

### 3b. Tighten (default for ads unless the user says otherwise)

Remove, inside each chosen take: **answer intros** ("Okay, I love this question. So", "Well,", "Yeah.", "That's a great question"), **fillers** (um, uh, er), **stutters/repeated words**, and **pauses** over ~0.3 s (closed to ~0.14 s). Keep spoken questions in Q&A formats unless told otherwise. Each removal becomes a jump cut, so a row turns into lettered segments (3a, 3b …).

Word timings alone can't find pauses: transcript engines (Frame.io included; check whether Premiere's are any better) stretch each word's duration over the pause after it, and their start times run 0.1–0.5 s early. So measure the audio:

1. **Local first.** Run `detect_silence` (Premiere MCP) on each take's source file, with `noise_threshold_db` -38 and `min_duration_seconds` 0.25. It runs on the user's PC (ffmpeg is installed there), returns silence intervals in clip-relative seconds, and needs no file transfer. A silence's end is the next speech onset, so use it for heads and pause cuts directly (steps 3–5), with the same word guard. If it errors with "ffmpeg was not found", the connector needs restarting (quit and reopen the Claude desktop app) or ffmpeg needs installing (`winget install Gyan.FFmpeg`).
   **Cloud fallback, and for heads in continuous speech:** request access to the edit folder, stage only the clips you need (≤3 per call), extract mono 16 kHz WAVs with ffmpeg in the cloud workspace, and use the envelope method below. You need this when a dropped word runs straight into a kept one with no silence (the level-jump cut in step 3), because `detect_silence` can't see that.
2. (Cloud envelope) Build a 10 ms dB envelope (30 ms smoothing). Per take: silence threshold = 5th percentile + 12 dB; speech level = median − 15 dB.
3. **Heads:** first sustained frame above speech level after the previous word, minus 0.06 s, rounded *down* to a source frame. If the previous (dropped) word runs straight into the first kept word with no silence ("Okay how…"), cut on the biggest level jump instead. Never reach back into the previous word.
4. **Pauses:** silences ≥ 0.30 s inside the take → remove [start + 0.07, end − 0.07], but never past a kept word's transcript start time (the guard that stops quiet words like "so", "if", "how", "here" from being cut).
5. **Intros/fillers:** remove from the silence before the dropped words to the silence before the next kept word (± 0.07 s).
6. **Check:** every kept word must overlap a kept segment. Print any lost word and fix before showing the sheet. Spot-check a few heads against the envelope (speech onset should sit 0–3 frames after the in point).

Untranscribed fillers can't be found this way. Say so in Checks.

**Two-camera podcasts / interviews:** take each speaker's lines from **their own** camera and audio. Measure the A/B offset once from words both mics picked up (the same word's onset on each camera's audio), record it in the sheet, and use it to map times between cameras.

### 4. Structure: hooks, body, nesting

When there are hook variations, build **one BODY sequence** (all body rows + CTA) and **one sequence per hook**: the hook take at 00:00:00:00, then the BODY sequence placed as a nested clip right after it. Premiere's scripting API can't nest clips in place (`nest_clips` is unavailable on CEP), so build the body as its own sequence and add it to each hook sequence as a project item. The result is the same: one body edit updates every hook.

**Naming (Hambi):** `[Brand]_HM_CM[campaign #]_[Ad Type]_C[concept #]_Hook[#]`, e.g. `PF_HM_CM2_HP_C2_Hook1`. Single-word brands use the whole name; multi-word brands use the initials (Pore Favor → PF). The body sequence is `…_C[#]_Body`. Campaign, ad type and concept number come from the ticket properties (Campaign, Ad Type, Concept #).

**Concept bin:** the hook and Body sequences always live in a concept bin named `[Ad Type] C[concept #]` (e.g. `HP C2`), from the ticket's Ad Type and Concept # properties. During inspection, look for a root-level bin named `Sequence`. If it exists, the concept bin goes inside it (`Sequence/HP C2`). If there's no `Sequence` bin, create the concept bin at the project root and mention that in the sheet. If the concept bin already exists (someone made it by hand), reuse it rather than creating a duplicate. Creating the bin is a project change, so it happens in step 9 after approval; the Execution plan lists it.

**Format:** default 1080×1920 (9:16) unless the ticket says otherwise. If the concept bin already holds an empty sequence (check which item is the bin and which is the sequence), rename that sequence and use it as Hook 1, then duplicate it for the others, so the team's sequence preset carries over. Otherwise create Hook 1 with `create_sequence`/`create_sequence_from_preset` and set it to the agreed format. Read the timebase: "24 fps" sequences are often 23.976. Use what's there and flag it.

### 5. Graphics, B-roll and text

- **Pass 1 (initial cut, no assets supplied):** don't place any real assets. Every visual direction in the ticket becomes a placeholder row with an ID (`P01`…), type **GFX** (graphic/animation), **BROLL** (cutaway), **TOS** (text on screen) or **LT** (lower third), the text to show, and the exact words it covers. On execution each placeholder becomes a **text box clip on the timeline**, not a marker. The clip spans the placeholder's in–out and shows `[TYPE] Pxx` plus the description (or the exact on-screen copy for TOS/LT).
  - **Tracks:** GFX/BROLL boxes go on **V2**, so the real B-roll later replaces them on the same track. TOS/LT boxes go on **V3**. Add tracks if they're missing.
  - **Clip label colours** (`set_color_label`): GFX purple, BROLL orange, TOS yellow, LT cyan. The only markers left are the green script-row markers (see 9.7).
  - **How the boxes are made** (`add_text_overlay` is unavailable on this MCP):
    1. **Preferred: text MOGRT.** Use a plain text `.mogrt`: a Hambi template if the user has one, else one exported once from Premiere's Essential Graphics (Basic Title) and kept in the edit folder at `Graphics/Placeholders/Placeholder_Text.mogrt`. Place it with `import_mogrt` (track, start, duration). Then set its text through `get_mogrt_component` → `set_effect_property` on the text parameter, and read it back. The result is a live text box the editor can retype.
    2. **Default without a MOGRT: placeholder caption track (SRT).** Proven on a full build. Write one SRT per sequence (`<sequence>_Placeholders.srt`) **in script mode**, from the sheet's placeholder table. Each placeholder is one cue spanning its in–out, with line 1 `[TYPE] Pxx <label>` and line 2 the copy or description. Placeholders that overlap in time **share one cue** (one block per placeholder inside it), because a caption track can't hold overlapping cues. Save the SRTs to `<edit folder>/Graphics/Placeholders/`; in execute mode, `import_media` them into `<concept bin>/Placeholders`, then `set_active_sequence` and `create_caption_track` (Subtitle, start 0) once per sequence. The cues are editable native text, and the editor can turn any of them into a graphic (right-click › Upgrade caption to graphic). Body placeholders show through the nest in every hook (they can only be edited inside the Body sequence). Limits: they share one caption style (no colour per type), and the CEP bridge can't read caption tracks back, so ask the user to check each sequence once by eye.
    3. **Last resort: PNG text cards.** Use these only if neither of the above works. Render transparent 1080×1920 cards with `scripts/placeholder_cards.py` (coloured border per type, positioned centre for GFX/BROLL, upper third for TOS, lower third for LT). Commit them to `<edit folder>/Graphics/Placeholders/`, `import_media` them into a `Placeholders` bin, and place them with `overwrite_clip` (or `add_to_timeline` if overwrite isn't available) on the track/time above, with the still's out point set first (`set_item_in_out`) so it lands at the placeholder duration. The text can't be retyped, so say so.
  - The script prompt says which method will be used. A switch between methods mid-build is reported.
  - Premiere's Type tool can't be driven from the MCP (`add_text_overlay` is unavailable and ExtendScript can't create or set Type-tool graphics), so a MOGRT is the only way to get live text boxes on V3. If the edit folder has no `Placeholder_Text.mogrt`, use the caption stopgap and remind the user once that exporting one (Type tool box › right-click › Export as Motion Graphics Template) unlocks text boxes.
- **If B-roll/assets are supplied up front**, map each to its placeholder (file + source in/out) and place it on V2+ with sync audio on A3+ muted, as part of the same approval.
- **Pass 2 (user supplies B-roll after seeing the cut):** issue v(N+1) of the script prompt that turns placeholders into placed rows (file, source in/out, timeline in/out, track), get approval, then duplicate the sequence and build on the copy.

### 5b. Subtitles (SRT, every cut with dialogue)

Every build also gets **subtitles**: an SRT per sequence, made from the kept words of the approved cut and imported as its own caption track (separate from any placeholder caption track). They are part of the approved version: the sheet shows them. **They're written in script mode** (step 7), from the sheet's planned timeline, and only imported in execute mode (step 9).

**Cue rules (Tim's house style):**
- A word's length is its **letter count**: punctuation, apostrophes and digits don't count. **Short** = 1–5 letters; **long** = 6+ letters. Numbers and prices (`£23`, `100`) count as short.
- A cue holds **up to 4 words if every word is short**, and **up to 2 words if any word is long**.
- A cue always ends at a sentence end (`.` `?` `!`) and at a script-row change (new speaker or take). A cue never ends on a weak word (`to`, `of`, `a`, `on`, `the`, `and`, `like`…) when that word fits at the start of the next cue.
- Text style: drop trailing commas and full stops, keep `?` and `!`, capitalise the first word of each row and sentence, and use UK spelling (unless the client is US).
- Apply the **Client standing notes** to the words, e.g. prices in currency format (`23 pounds` → `£23`, `50 to 100 pounds` → `£50 to £100`). A bare number that is a price in context (`100`, `120` as price guesses) gets the symbol via the corrections table.

**Timing:** each cue starts on its first word's timeline time (snapped down to a frame). It runs to the next cue when the gap is under 0.5 s (no flicker), otherwise to the last word's end + 0.1 s. Minimum 6 frames, no overlaps. Word times come from the transcript, mapped through the segment table: timeline = start_frame × T + (word − in_s), clamped inside the segment.

**Corrections table:** list every word the subtitles change from the transcript, as `row · heard → shown`: mishearings (`room` → `Rome`), words the transcript dropped (`working` → `wearing it`), fillers it heard as words (`are` → removed, written as an empty correction), brand capitals (`noted` → `Noted`), UK spellings (`favorite` → `favourite`) and price symbols (`100` → `£100`). These feed the helper's `fixes`, and the sheet shows the table so the user can approve the wording.

**Which files (one source of truth per line of dialogue):**
- `<Body>_Subtitles.srt`: the Body's cues, on the Body sequence only.
- `<HookN>_Subtitles.srt`: **only that hook's own cues**, from 00:00:00:00 to the end of the hook. The Body's subtitles are never copied into a hook. Each line is subtitled once, so a wording fix in the Body never has to be repeated in three hooks.
- The Body's captions show through the nest when a hook plays. They're read-only there and are edited inside the Body sequence, which is the normal way of working, so nothing is duplicated or converted.
- Files go in `<edit folder>/Graphics/Subtitles/` and the `<concept bin>/Subtitles` bin.

**Cue map (lets execute mode re-time without transcripts):** for every cue, record which segment it belongs to and its in/out relative to that segment's start (`cue, seq, seg, rel_in_s, rel_out_s, text`) in the Execution data. In execute mode, if a sequence's built length differs from the sheet (Premiere conformed a segment to a different frame count, or the editor trimmed something), regenerate **only that sequence's** SRT: new cue time = the segment's actual start + rel time, clamped to the segment's actual length; drop and report any cue that no longer fits. No transcript is needed.

**Checks:** run `check()` on every SRT, which must return no violations. Show the first ~12 Body cues and each hook's cues in the sheet as a preview, plus the cue count per sequence.

### 6. Inspect Premiere (read-only)

`ping`, `get_project_info`, `list_project_items` (note whether a root `Sequence` bin and the concept bin exist; walk bins with `bin_path`, e.g. `Footage/C2/BLOCK 1`; this MCP labels bins as "sequence", so recurse by name), `get_project_item_info` to confirm every clip exists (exact names + node IDs), its fps and its start timecode. Frame.io names are often proxies (`C0002_1.mp4`); if Premiere has the originals (`C0002.MP4`), map by start timecode and duration and show the mapping. Also note which clips already have a Premiere transcript (`has_transcript_uxp`) and whether the UXP bridge answers. If the bridge is down (stale heartbeat), still draft the script prompt, mark the check ⏳ pending, and re-verify before executing. The fix is to reopen Window > Extensions > MCP Bridge in Premiere.

### 7. Write and deliver the script prompt

Use the template below. Timecodes in the readable tables are **source camera timecode** (what Frame.io and Premiere's source monitor show) and **timeline timecode** per sequence. Put clip-relative seconds and everything else the build needs in the "Execution data" section at the end: execute mode reads only that section.

Deliver it in four places:
1. **Notion:** one sub-page of the ticket, retitled per version: `Script Prompt v<N> — <sequence base name> (awaiting approval)`. Replace its content on each new version (the .md holds the full Execution data). Notion needs `<table header-row="true"><tr><td>…</td></tr></table>` tables, not pipe tables, and blank lines between header fields. On approval or a new version, update the title/status rather than creating duplicates.
2. **Markdown file:** `<sequence base name>_ScriptPrompt_v<N>.md` (e.g. `PF_HM_CM2_HP_C2_ScriptPrompt_v2.md`) in the edit folder's `Script Prompts` subfolder (ask for the edit folder if unknown; the .prproj path from `get_project_info` usually sits in it). Execute mode reads this file, so it must hold the full Execution data.
3. **SRT files:** the subtitle SRTs (`<edit folder>/Graphics/Subtitles/<sequence>_Subtitles.srt`) and, when no MOGRT is used, the placeholder SRTs (`<edit folder>/Graphics/Placeholders/<sequence>_Placeholders.srt`). Create the folders if needed. Each new version overwrites its own SRTs, and the sheet lists their paths in Execution data.
4. **Chat:** a short summary with the link, the runtime, the ⚠️ items and the open questions, not the whole table. Don't re-print the sheet. End with the hand-off reminder (step 7b).

### 7b. Hand-off reminder (end of every script-mode reply that delivers or approves a version)

Close every reply that delivers a version, and every approval in the script chat, with this block, filled in with the real version and the full path to the .md:

> **Next: build in a new chat.** Reply "APPROVED v<N>" here if you haven't yet, then start a **new chat** and paste:
> `APPROVED v<N>. Execute from <full path to …_ScriptPrompt_v<N>.md>. Skip preflight.`
> A fresh chat keeps the build fast and cheap; this chat holds all the transcript context the build doesn't need.

When the user approves in the script chat, confirm the approval, update the sheet's status, and repeat the block. Don't start building unless they explicitly ask to build in this chat.

### 8. Validate (before every approval request)

Run the checks with the helper rather than by eye. Call `validate()` once per sequence (filter rows by the Seq column), and pass clip end times in the same timecode base as the table (camera TC start + duration):

- Timecodes parse; in < out; frames < fps; everything snapped to frames.
- Source in/out lies within the clip's duration; chosen ranges sit inside or close to the Frame.io comment range (explain any >2 s departure).
- Clip names match project items (or the proxy→original mapping).
- BODY/V1 rows are contiguous; runtime per sequence vs target; flag a runtime far over the format norm.
- Slate proximity (⚠️ if ≤3 frames between "action" and the first word).
- Client standing notes are met, or the conflict is an open question.
- Mode B: picture duration vs VO line duration.

### 9. Execute mode (fresh chat, approved version only)

Execute mode runs in its own chat, started with `APPROVED v<N>. Execute from <path>. Skip preflight.` Work only from the sheet's Execution data. Keep every tool result small: prefer summaries, never re-print the sheet or long tool output in chat.

0. **Load the sheet, no preflight.** Read the .md at the given path with the local file tool and parse the Execution data (build settings, segments, placeholders, markers, cue map, SRT paths). Check that its version matches the approved one; if the user's message names a different version, stop and ask. Then one `ping` + `get_project_info` to confirm the right project is open. Don't run the preflight table, pull transcripts, open Frame.io or re-read the ticket. If the sheet has no Execution data block (an older sheet), say so and ask whether to run script mode for it instead.
1. `create_project_backup` on the .prproj.
2. **Concept bin.** If there's a root `Sequence` bin and it has no `[Ad Type] C[#]` bin yet, `create_bin` it with `parent_bin` = the Sequence bin's node ID (or at the root if there's no Sequence bin). Confirm with `list_project_items` (`bin_path` = `Sequence/HP C2`). Every sequence created, duplicated or renamed below ends up in this bin.
3. **Sequences.**
   - `list_project_items` labels bins as "sequence" too, so before renaming anything, check it with `get_item_info` (`isSequence`, `treePath`). A name like "HP C2" is often a *bin* holding the real sequence ("Sequence 02"). Rename the sequence item, never the bin; confirm with `list_sequences` that the sequence name changed (`sequenceVerified: true`).
   - **Creating Hook 1** when the concept bin has none: `create_sequence` uses the UHD 25 fps default preset, so straight after creating it, `set_sequence_settings` to 1080×1920 (or the sheet's format), then `set_sequence_frame_rate` with **23.976023976023978**. Passing `23.976` gives the wrong timebase (10594594595 ticks per frame instead of 10594584000). The frame-rate call acts on the active sequence, so `set_active_sequence` first, and confirm with `get_sequence_settings` **by sequence ID**. Do this before placing anything.
   - Duplicate Hook 1 (`duplicate_sequence`) for the other hooks and the Body, rename the copies, move them all into the concept bin, and confirm each copy's settings by ID.
4. **Use the footage as provided: no subclips, no copies.** The cut is built straight from the user's own clips in their Footage bins. Never `create_subclip`, duplicate, re-import or transcode footage, and never create a footage bin (e.g. `C2_ScriptCut`). The only new project items a build may create are the concept bin, sequences, placeholder/subtitle files (SRT, PNG, MOGRT) and the backup. Before placing, note each source clip's existing in/out marks (`get_item_info`) so they can be restored afterwards.
5. **Frame conform.** When source and sequence rates differ, Premiere floors each source in and out to the *sequence* frame grid on placement: frames = floor(out ÷ T) − floor(in ÷ T), where T = sequence frame duration (1001/24000 at 23.976). Lay out start times from those frame counts, not from rounded durations. Otherwise each insert splits the previous clip and leaves a 1-frame fragment.
6. **Placement.**
   - Every tool that takes a `sequence_id` (even read-only ones like `get_timeline_gaps`) silently makes that sequence active, and inserts go to whichever sequence is active. So call `set_active_sequence` immediately before each run of `add_to_timeline` calls, with no other sequence queries in between.
   - **Placing a segment from the original clip:** `set_item_in_out` on the source clip with the **out point first, then the in point** (two calls), then `add_to_timeline` with that clip's node ID at the segment's start. Do one segment at a time in timeline order. Don't use `add_to_timeline_batch` for this, because every placement of the same clip needs its own in/out set just before it.
   - **If `set_item_in_out` refuses a valid value** (seen: 33.16 s refused, 33.20 s accepted), try one source frame later, then one earlier, and record the deviation (segment, planned vs used) for the close-out report and the sheet.
   - **Read back** with `get_timeline_summary` after each segment (or each few segments on long bodies): clip count, last clip's start and duration. Use `get_sequence_structure` only when you need track-item node IDs.
   - **If a placed item is wrong** (whole clip placed, wrong length, extra copy): remove that one track item and re-add it after setting the in/out again. `trim_clip` doesn't work on this Premiere build, so never use it to fix a placement.
   - **Duplicate runs:** the bridge sometimes executes a call twice. If the read-back shows extra clips, `select_clips_in_range` over just the extras and `remove_selected_clips` (no ripple), confirming the selection holds only the extras.
   - Place the Body segments into the Body sequence, then in each hook sequence place the hook segment(s) from 0 and the Body sequence item straight after.
   - **Scale:** when the footage is larger than the sequence, scale the placed track items, not the project items (see Pitfalls: `set_clip_properties_batch` with a Motion scale).
   - **Restore the source clips:** when placement is done, `clear_item_in_out` on every source clip used, or put back the marks noted in step 4. The Footage bins should end up exactly as they started.
7. **Placeholders, row markers and subtitles.**
   - **Timing.** Use full-precision frame times (k × T, not rounded seconds) for every start and duration.
   - **Placeholders.** Body placeholders go into the Body sequence, so they carry into every hook through the nest; hook-only placeholders go into their own hook sequence.
     - Caption route (default without a MOGRT): `import_media` the ready-made `<sequence>_Placeholders.srt` from the paths in Execution data into `<concept bin>/Placeholders`, then `set_active_sequence` and `create_caption_track` (Subtitle, start 0) once per sequence.
     - MOGRT route: make sure V2/V3 exist (`add_track`), `import_mogrt` per box, then set and read back its text; `set_color_label` per type.
     - PNG route: see step 5.
   - **Row markers.** One green marker per script row (name `L03 Body 1`, comment = the line), added with `manage_markers_uxp` and an explicit `sequence_id`, which works without changing the active sequence. Check the marker count per sequence afterwards.
   - **Subtitles.** First compare each sequence's built length (`get_timeline_summary`) with the sheet. If they match, import the ready-made SRT as is. If not, regenerate **only that sequence's** SRT from the cue map (step 5b) and save it over the old one, then report it. `import_media` the SRTs into `<concept bin>/Subtitles` (list the bin afterwards: one item per file), then `set_active_sequence` and `create_caption_track` (Subtitle, start 0) once per sequence.
   - **Caption-track duplicates:** check each sequence with `inspect_caption_tracks_uxp`. Caption tracks can't be deleted through the bridge, so if a sequence shows a doubled track, tell the user which sequence and ask them to delete the extra by hand.
8. **Verify** every sequence with `get_timeline_summary` and `get_timeline_gaps` at 0.01 s on V1: V1 clip counts, total frames vs plan, no gaps, placeholder and caption tracks present, marker counts. Then `save_project`.
9. **Close out.** Mark the sheet `APPROVED v<N> · EXECUTED <date>` (with the backup name, bin locations and any deviations, such as in/out values nudged by a frame or SRTs regenerated), re-save it to the edit folder, retitle the Notion page `(EXECUTED)`, and report the sequences, runtimes, deviations and the placeholder list in a few lines.

If a tool fails or a read-back doesn't match mid-way, stop, report exactly what was and wasn't built, and fix only what you placed. Remove your own track items, never anything that was there before, and say what you removed. Don't swap to a different editing method without saying so. Undo isn't available through the MCP, which is one more reason the backup in step 1 is mandatory.

## Frame.io extraction

Frame.io's public API doesn't expose transcripts, but the web app loads them through its own GraphQL API (`api.frame.io/graphql`), which you can read from the signed-in browser tab. Steps, using the built-in browser (`Claude_Browser__*`):

1. `request_access` for `https://next.frame.io` (scope "site"), open any shot link with `preview_start`, and confirm it isn't a sign-in page.
2. With `javascript_tool`, wrap `window.fetch` to record GraphQL responses by `operationName`, then switch assets **inside the single-page app** (`window.next.router.push('/project/<project>/view/<assetId>')`) so the wrapper survives. A full navigation would reset it.
3. For each asset, read:
   - `GetAssetForHeader`: `name`, `fps`, `timecode` (start TC), `duration`.
   - `GetCommentsByAsset`: per comment, `text`, `timestampMicroseconds` (start, clip-relative) and `duration` (seconds; null for a point comment).
   - `GetTranscriptionStreamUrl`: `localeTranscriptions.nodes[0].json.streamUrl`. Fetch it to get `{"words":[{text, offset(ms), duration(ms), speaker, tags}]}`, clip-relative and word-level. Punctuation tokens carry `tags: ["punctuation"]` (+`"end_of_sentence"`). Speaker IDs are unreliable across clips, so ignore them.
4. Compact the result in the page (`[text, offset, duration]` arrays) before returning it, because a full transcript set is large. To get it into the workspace as a file, return it padded past the tool-result size limit so it's saved to disk, then parse it there.

```js
// 1) install once per tab
window.__cap=[]; const of=window.fetch;
window.fetch=async function(i,o){const r=await of.apply(this,arguments);
  try{const u=typeof i==='string'?i:i.url; if(u.includes('graphql')){const b=o&&o.body?String(o.body):'';
    r.clone().text().then(t=>window.__cap.push({op:(b.match(/"operationName":"(\w+)"/)||[])[1],resp:t}));}}catch(e){} return r;};
// 2) per asset
async function grab(project, id){
  const n0=__cap.length; window.next.router.push(`/project/${project}/view/${id}`);
  let h,c,t; for(let k=0;k<20&&!(h&&c&&t);k++){await new Promise(r=>setTimeout(r,700)); const cs=__cap.slice(n0);
    h=cs.filter(x=>x.op==='GetAssetForHeader'&&x.resp.includes(id)&&x.resp.includes('"fps"')).pop();
    c=cs.filter(x=>x.op==='GetCommentsByAsset'&&x.resp.includes(id)).pop();
    t=cs.filter(x=>x.op==='GetTranscriptionStreamUrl'&&x.resp.includes(id)).pop();}
  const o={id};
  if(h){o.name=(h.resp.match(/"name":"([^"]+\.(?:mp4|mov|mxf|wav))"/i)||[])[1]; o.fps=+(h.resp.match(/"fps":([\d.]+)/)||[])[1];
        o.tc=(h.resp.match(/"timecode":"([^"]+)"/)||[])[1]; o.dur=+(h.resp.match(/"duration":([\d.]+)/)||[])[1];}
  if(c) o.comments=JSON.parse(c.resp).data.asset.comments.result.map(x=>({text:x.text,start:x.timestampMicroseconds/1e6,dur:x.duration}));
  if(t){const u=JSON.parse(t.resp).data.asset.localeTranscriptions.nodes[0].json.streamUrl;
        o.w=JSON.parse(await (await fetch(u)).text()).words.map(x=>[x.text,x.offset,x.duration]);}
  return o;
}
```

If a field is missing (e.g. the header response didn't match), read it from the page text instead: the player shows the start TC when paused at the head, and the comment list shows camera-TC ranges. If there's no transcript, Frame.io hasn't generated one. Ask the user to click Transcribe on those assets, or fall back to local Whisper.

## Script prompt template

```markdown
# Script Prompt: <Brand · Concept>, v<N>
**Status:** DRAFT, awaiting approval
**Source ticket:** <link> · <which script section was used and why>
**Mode:** A | B · **Deliverable:** Initial cut (placeholders) | Full edit
**Sequences:** <BODY>, <H1>, <H2> in bin <Sequence/[Ad Type] C[#]> · <fps> fps · <W×H> · TC = HH:MM:SS:FF
**Source TC:** camera timecode; clip-relative seconds in Execution data
**Transcript source:** <Premiere native | Frame.io word-level | SRT | Whisper> (+ Frame.io comments for take references)
**Runtime:** <per sequence> · target <x>
**Due:** <date>
**Edit folder:** <full path> · **Sheet file:** <full path to this .md>

## Client standing notes
- <rule> → <how it's applied / conflict>

## Sources
| ID | Clip | Role | Start TC | Duration | Frame.io comment (marked range) |

## Script: A-roll (V1/A1)
| # | Seq | Section | Line (heard) | Src | Source in – out | Timeline in – out | Notes |

## Placeholders: graphics, B-roll, text (pass 1)
### <Sequence>
| ID | Timeline in – out | Track | Type | Box text / what goes here |

Text boxes via: MOGRT `<path>` | placeholder caption track (SRT stopgap) | PNG cards (`Graphics/Placeholders/`)

## Subtitles (SRT)
Rule: ≤4 words per cue if all words are 1–5 letters; ≤2 words if any word is 6+ letters · files in `Graphics/Subtitles/`
| Sequence | File | Cues | check() |

### Corrections (transcript → subtitle)
| Row | Heard | Shown | Why |

### Preview
| Sequence | In – out | Cue |

## Alternates & removed takes
| Beat | Clip | Source in – out | Why not used |

## Checks
- ✅ / ⚠️ / ❌ / ⏳ one line each

## Execution plan (runs only after approval)
1. … numbered build steps (backup, concept bin, sequences, placement from the original clips, placeholders, row markers, subtitles, verify). Runs in execute mode, in a new chat.

## Open questions
1. <only what blocks or materially changes the cut>

**Reply "APPROVED v<N>", or send changes. Then start a new chat and paste:**
`APPROVED v<N>. Execute from <full path to this .md>. Skip preflight.`

---
## Execution data (everything execute mode needs; it reads nothing else)

### Build settings
| Key | Value |
|---|---|
| Version | v<N> |
| Project | <full .prproj path> |
| Edit folder | <full path> |
| Notion page | <script-prompt sub-page URL> |
| Concept bin | <Sequence/[Ad Type] C[#]> (exists: yes/no) |
| Sequences | <Hook1 name>, <Hook2 name>, <Body name> (existing sequence to rename, if any) |
| Format | 1080×1920 · 23.976023976023978 fps · T = 1001/24000 s |
| Placeholder method | caption SRT \| MOGRT `<path>` \| PNG |
| Placeholder SRTs | <full paths, one per sequence> |
| Subtitle SRTs | <full paths, one per sequence> |
| Planned length | <sequence: frames>, … |

### Segments (clip-relative seconds)
| Seg | Sequence | Source clip (name) | Project item node ID | Clip fps | in_s | out_s | start_frame | frames | Track |

### Placeholders
| ID | Sequence | Type | start_frame | frames | Track | Text |

### Row markers
| Sequence | Name | start_frame | Comment |

### Subtitle cue map
| Cue | Sequence | Seg | rel_in_s | rel_out_s | Text |
```

## Timecode helper

Write this to the scratchpad and import it. It parses SRT/VTT/timestamped TXT/Whisper JSON, converts timecodes (including 29.97/59.94 drop-frame and 23.976), and validates a script table.

```python
import re, json, math, hashlib

def _nominal(fps): return round(fps)

def tc_to_sec(tc, fps):
    """'HH:MM:SS:FF' / 'HH:MM:SS;FF' (drop-frame) / 'HH:MM:SS.mmm' / 'HH:MM:SS,mmm' / 'MM:SS' -> seconds."""
    tc = tc.strip()
    m = re.fullmatch(r'(\d+):(\d{2}):(\d{2})([:;])(\d{2})', tc)
    if m:
        h, mi, s, sep, f = int(m[1]), int(m[2]), int(m[3]), m[4], int(m[5])
        n = _nominal(fps)
        if f >= n: raise ValueError(f'frame {f} >= {n} in {tc}')
        frames = (h*3600 + mi*60 + s)*n + f
        if sep == ';':  # drop-frame
            drop = 2 if n == 30 else 4
            total_min = h*60 + mi
            frames -= drop*(total_min - total_min//10)
        return frames / fps
    m = re.fullmatch(r'(?:(\d+):)?(\d{1,2}):(\d{2})(?:[.,](\d{1,3}))?', tc)
    if m:
        h = int(m[1] or 0); ms = int((m[4] or '0').ljust(3, '0'))
        return h*3600 + int(m[2])*60 + int(m[3]) + ms/1000
    raise ValueError(f'bad timecode: {tc}')

def sec_to_tc(sec, fps, drop=False):
    n = _nominal(fps); frames = int(round(sec*fps))
    if drop and n in (30, 60):
        d = 2 if n == 30 else 4; per10 = n*600 - d*9; per1 = n*60 - d
        tens, rem = divmod(frames, per10)
        frames += d*9*tens + (d*((rem - d)//per1) if rem > d else 0)
    f = frames % n; s = frames//n
    return f'{s//3600:02d}:{s//60%60:02d}:{s%60:02d}{";" if drop else ":"}{f:02d}'

def parse_transcript(path):
    """Returns [{'id','start','end','speaker','text'}] in seconds."""
    raw = open(path, encoding='utf-8-sig').read()
    if path.lower().endswith('.json'):  # Whisper / faster-whisper JSON
        d = json.load(open(path)); segs = d.get('segments', d)
        return [{'id': f'seg{i+1}', 'start': s['start'], 'end': s['end'],
                 'speaker': s.get('speaker'), 'text': s['text'].strip(),
                 'words': s.get('words')} for i, s in enumerate(segs)]
    out = []
    cue = re.compile(r'([\d:.,]+)\s*-->\s*([\d:.,]+)[^\n]*\n(.*?)(?:\n\s*\n|\Z)', re.S)
    for i, m in enumerate(cue.finditer(raw)):  # SRT / VTT
        text = re.sub(r'<[^>]+>', '', m[3]).strip().replace('\n', ' ')
        spk = None
        sm = re.match(r'^(?:\[([^\]]+)\]|([A-Z][\w .]{0,30}):)\s*(.*)$', text)
        if sm and (sm[1] or sm[2]): spk, text = (sm[1] or sm[2]).strip(), sm[3]
        out.append({'id': f'seg{i+1}', 'start': tc_to_sec(m[1], 30), 'end': tc_to_sec(m[2], 30),
                    'speaker': spk, 'text': text})
    if out: return out
    # Timestamped TXT: lines like "[00:01:02] Speaker 1: text" or "00:01:02.500 text"
    stamp = re.compile(r'^\[?(\d{1,2}:\d{2}(?::\d{2})?(?:[.,]\d+)?)\]?\s*(?:-\s*)?(?:([^:\n]{1,40}):\s+)?(.*)$')
    for line in raw.splitlines():
        m = stamp.match(line.strip())
        if m and m[3]:
            out.append({'start': tc_to_sec(m[1], 30), 'speaker': m[2], 'text': m[3].strip()})
        elif out and line.strip():
            out[-1]['text'] += ' ' + line.strip()
    for i, s in enumerate(out):
        s['id'] = f'seg{i+1}'
        s['end'] = out[i+1]['start'] if i+1 < len(out) else s['start'] + max(1.0, len(s['text'].split())/2.6)
    return out

def transcript_revision(segments):
    blob = json.dumps([[s['start'], s['end'], s['text']] for s in segments], sort_keys=True)
    return 'sha256:' + hashlib.sha256(blob.encode()).hexdigest()

def parse_md_table(md, header_startswith='| #'):
    lines = [l for l in md.splitlines() if l.strip().startswith('|')]
    start = next(i for i, l in enumerate(lines) if l.strip().startswith(header_startswith))
    hdr = [h.strip() for h in lines[start].strip('|').split('|')]
    rows = []
    for l in lines[start+2:]:
        cells = [c.strip() for c in l.strip().strip('|').split('|')]
        if len(cells) != len(hdr) or not cells[0][:1].isdigit(): break
        rows.append(dict(zip(hdr, cells)))
    return rows

def split_range(r):
    a, b = re.split(r'\s+[–-]\s+', r.strip()); return a, b

def validate(rows, fps, clip_durations, target=None, mode='A'):
    """clip_durations: {source_id_or_name: seconds}. Returns (errors, warnings, runtime)."""
    errs, warns, prev_out = [], [], 0.0
    for r in rows:
        n = r['#']
        if 'Source in – out' in r:  # A-roll template: one source column, picture = audio
            if r.get('Src') in ('—', '-', ''): continue  # nested-sequence rows
            r.setdefault('Audio in – out', r['Source in – out']); r.setdefault('Picture in – out', r['Source in – out'])
            r.setdefault('Audio src', r.get('Src')); r.setdefault('Picture src', r.get('Src'))
        for col, src in (('Audio in – out', r.get('Audio src')), ('Picture in – out', r.get('Picture src'))):
            v = r.get(col, '')
            if '⟨' in v or '⟨' in (src or ''): errs.append(f'Row {n}: {col} not filled'); continue
            try: a, b = map(lambda t: tc_to_sec(t, fps), split_range(v))
            except Exception as e: errs.append(f'Row {n}: {col} {e}'); continue
            if a >= b: errs.append(f'Row {n}: {col} in >= out')
            dur = clip_durations.get(src)
            if dur is None and src not in ('VO',): warns.append(f'Row {n}: source {src} not found in project')
            elif dur is not None and b > dur + 1/fps: errs.append(f'Row {n}: {col} out {v} exceeds clip length')
        try:
            ti, to = map(lambda t: tc_to_sec(t, fps), split_range(r['Timeline in – out']))
            if r.get('Trk', 'V1').startswith('V1'):
                if abs(ti - prev_out) > 0.5/fps:
                    warns.append(f'Row {n}: {"gap" if ti > prev_out else "overlap"} of {abs(ti-prev_out):.2f}s on V1')
                prev_out = to
            ai, ao = map(lambda t: tc_to_sec(t, fps), split_range(r['Audio in – out']))
            pi, po = map(lambda t: tc_to_sec(t, fps), split_range(r['Picture in – out']))
            if mode == 'B' and abs((po-pi) - (ao-ai)) > 0.5/fps:
                warns.append(f'Row {n}: picture {(po-pi):.2f}s vs VO line {(ao-ai):.2f}s')
        except Exception:
            pass
    if target and abs(prev_out - target) > 1:
        warns.append(f'Runtime {prev_out:.1f}s vs target {target:.1f}s')
    return errs, warns, prev_out
```

SRT/VTT timestamps are real milliseconds, so the fps passed while parsing them doesn't matter; convert to frames with `sec_to_tc(sec, sequence_fps)` when writing the script prompt. Snap every in/out to whole frames before validation and execution.

## Subtitle helper

Write this to the scratchpad as `subtitles.py` next to the timecode helper. Its inputs are the Execution data segments for one sequence (`seg`, `clip`, `in_s`, `out_s`, `start_frame`, `row`, from the sheet's planned layout; it runs in script mode) and the word-level transcripts per clip (`[[text, offset_ms, dur_ms], …]`, the Frame.io format; convert a Premiere transcript to the same shape). Alongside each SRT, write the cue map rows (cue, sequence, segment, rel_in_s, rel_out_s, text) into the sheet's Execution data, so execute mode can re-time cues without transcripts.

```python
import re

LONG = 6          # letters; a word with >= LONG letters is "long"
MAX_SHORT = 4     # max words per cue when every word is short (<= 5 letters)
MAX_LONG = 2      # max words per cue when any word is long (>= 6 letters)
GAP_HOLD = 0.5    # s; hold a cue until the next one if the gap is shorter than this
TAIL = 0.10       # s; after the last word when the next cue is far away
MIN_DUR = 0.24    # s; shortest cue

def letters(w):
    return sum(ch.isalpha() for ch in w)

def is_long(w):
    return letters(w) >= LONG

def clean(tok):
    """Caption text for a word: drop trailing commas/full stops, keep ? and !"""
    return re.sub(r'[.,;:]+$', '', tok)

def currency(words, symbol='£', unit=r'pounds?'):
    """Merge 'N pounds' -> '£N' and 'N to/or M pounds' -> '£N to/or £M'.
    words: list of dicts with 'text','start','end'. Returns a new list."""
    out, i = [], 0
    num = re.compile(r'^\d+([.,]\d+)?$')
    while i < len(words):
        w = words[i]; t = clean(w['text'])
        nxt = lambda k: clean(words[i+k]['text']).lower() if i+k < len(words) else ''
        if num.match(t) and re.fullmatch(unit, nxt(1)):
            out.append({**w, 'text': symbol + t, 'end': words[i+1]['end'], 'eos': words[i+1].get('eos')}); i += 2; continue
        if num.match(t) and nxt(1) in ('to', 'or', '-') and num.match(nxt(2)) and re.fullmatch(unit, nxt(3)):
            out.append({**w, 'text': symbol + t})
            out.append({**words[i+1], 'text': nxt(1)})
            out.append({**words[i+2], 'text': symbol + nxt(2), 'end': words[i+3]['end'], 'eos': words[i+3].get('eos')})
            i += 4; continue
        out.append(w); i += 1
    return out

def timeline_words(segs, transcripts, fps, fixes=None):
    """segs: ordered segments of ONE sequence, each {'clip','in_s','out_s','start_frame','row'}.
    transcripts: {clip: [[text, offset_ms, dur_ms], ...]} word-level (punctuation tokens allowed).
    fixes: {(row, heard_text): correct_text}. The value may be several words ('wearing it'),
    which share the heard word's time, so dropped words can be put back; '' drops the word.
    Returns kept words with timeline seconds, in order."""
    T = 1.0 / fps; fixes = fixes or {}; out = []
    words = {}
    for clip, toks in transcripts.items():
        ws = []
        for txt, off, dur in toks:
            if txt.strip() in ('.', ',', '?', '!', ';', ':'):
                if ws:
                    if txt in '?!': ws[-1]['p'] = txt
                    if txt in '.?!': ws[-1]['eos'] = True
                continue
            ws.append({'text': txt, 'a': off / 1000, 'b': (off + dur) / 1000})
        words[clip] = ws
    for s in segs:
        t0 = s['start_frame'] * T
        for w in words[s['clip']]:
            if not (s['in_s'] - 0.05 <= w['a'] < s['out_s']): continue
            a = max(w['a'], s['in_s']); b = min(w['b'], s['out_s'])
            parts = fixes.get((s['row'], w['text']), w['text']).split()
            if not parts:                      # an empty fix drops the word
                if w.get('eos') and out and out[-1]['row'] == s['row']: out[-1]['eos'] = True
                continue
            step = (b - a) / len(parts)
            for k, p in enumerate(parts):
                last = k == len(parts) - 1
                out.append({'text': p + (w.get('p', '') if last else ''),
                            'start': t0 + a + k * step - s['in_s'], 'end': t0 + a + (k + 1) * step - s['in_s'],
                            'row': s['row'], 'eos': w.get('eos') and last})
    # capitalise the first word of each row and of each sentence
    for i, w in enumerate(out):
        if i == 0 or out[i-1]['row'] != w['row'] or out[i-1].get('eos'):
            w['text'] = w['text'][:1].upper() + w['text'][1:]
    return out

WEAK = {'a', 'an', 'the', 'to', 'of', 'on', 'or', 'and', 'is', 'my', 'your', 'for', 'in', 'at', 'so', 'but', 'like'}

def _limit(ws):
    return MAX_LONG if any(is_long(x['text']) for x in ws) else MAX_SHORT

def chunk(words):
    """Greedy cues: up to 4 words, or up to 2 if any word in the cue has 6+ letters.
    A cue always ends at a sentence end or a script-row change, and never ends on a
    weak word (to, of, a, on...) when that word fits at the start of the next cue."""
    cues, cur = [], []
    for w in words:
        if cur:
            cand = cur + [w]
            if len(cand) > _limit(cand) or cur[-1]['row'] != w['row'] or cur[-1].get('eos'):
                cues.append(cur); cur = []
        cur.append(w)
    if cur: cues.append(cur)
    for i in range(len(cues) - 1):
        c, n = cues[i], cues[i+1]
        if len(c) > 1 and clean(c[-1]['text']).lower() in WEAK and c[-1]['row'] == n[0]['row'] \
                and not c[-1].get('eos') and len(n) + 1 <= _limit([c[-1]] + n):
            n.insert(0, c.pop())
    return cues

def timed(cues, fps, seq_end):
    T = 1.0 / fps
    snap_dn = lambda x: int(x / T + 1e-6) * T
    snap_up = lambda x: -int(-x / T + 1e-6) * T
    out = []
    for i, c in enumerate(cues):
        a = snap_dn(c[0]['start'])
        nxt = snap_dn(cues[i+1][0]['start']) if i + 1 < len(cues) else seq_end
        b = snap_up(c[-1]['end'])
        b = nxt if nxt - b < GAP_HOLD else min(snap_up(b + TAIL), nxt)
        if b - a < MIN_DUR: b = min(snap_up(a + MIN_DUR), nxt)
        if out and a < out[-1][1]: a = out[-1][1]
        out.append((a, max(b, a + T), ' '.join(clean(w['text']) if not w['text'].endswith(('?', '!')) else w['text'] for w in c)))
    return out

def srt(cues):
    def ts(s):
        ms = round(s * 1000); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); sec, ms = divmod(ms, 1000)
        return f'{h:02d}:{m:02d}:{sec:02d},{ms:03d}'
    return '\n'.join(f'{i}\n{ts(a)} --> {ts(b)}\n{t}\n' for i, (a, b, t) in enumerate(cues, 1))

def check(cues):
    """Returns rule violations (should be empty)."""
    bad = []
    for a, b, t in cues:
        ws = t.split()
        lim = MAX_LONG if any(is_long(w) for w in ws) else MAX_SHORT
        if len(ws) > lim: bad.append(f'{a:.2f}: "{t}" has {len(ws)} words (max {lim})')
        if b <= a: bad.append(f'{a:.2f}: zero length')
    for (a1, b1, _), (a2, _, _) in zip(cues, cues[1:]):
        if a2 < b1 - 1e-6: bad.append(f'{a2:.2f}: overlaps previous cue')
    return bad

def subtitles(segs, transcripts, fps, seq_end, fixes=None, currency_symbol='£', offset_frames=0):
    """One sequence -> list of (start_s, end_s, text). offset_frames shifts segs (rarely needed)."""
    segs = [{**s, 'start_frame': s['start_frame'] + offset_frames} for s in segs]
    w = timeline_words(segs, transcripts, fps, fixes)
    if currency_symbol: w = currency(w, currency_symbol)
    return timed(chunk(w), fps, seq_end)

def cue_map(cues, segs, fps, seq):
    """Script mode: tie each cue to the segment it starts in -> rows for the sheet's Subtitle cue map."""
    T = 1001/24000 if abs(fps - 23.976) < 0.01 else 1.0 / fps
    rows = []
    for i, (a, b, t) in enumerate(cues, 1):
        s = max((x for x in segs if x['start_frame'] * T <= a + 1e-6), key=lambda x: x['start_frame'])
        s0 = s['start_frame'] * T
        rows.append({'cue': i, 'seq': seq, 'seg': s['seg'], 'rel_in_s': round(a - s0, 4), 'rel_out_s': round(b - s0, 4), 'text': t})
    return rows

def retime(rows, actual, fps):
    """Execute mode: actual = {seg: (start_frame, frames)} read back from the built timeline.
    Returns (cues, dropped). Needs no transcript."""
    T = 1001/24000 if abs(fps - 23.976) < 0.01 else 1.0 / fps
    cues, dropped = [], []
    for r in rows:
        if r['seg'] not in actual: dropped.append(r); continue
        sf, n = actual[r['seg']]
        s0, seg_len = sf * T, n * T
        if r['rel_in_s'] >= seg_len - T: dropped.append(r); continue
        a = s0 + r['rel_in_s']
        b = s0 + min(r['rel_out_s'], seg_len) if r['rel_out_s'] <= seg_len else s0 + seg_len
        if cues and a < cues[-1][1]: cues[-1] = (cues[-1][0], a, cues[-1][2])
        cues.append((a, max(b, a + T), r['text']))
    return cues, dropped
```

Usage per project:

```python
fixes = {('H1', 'room'): 'Rome', ('24', 'working'): 'wearing it', ('17', '100'): '£100', ('16', 'are'): ''}   # from the corrections table
body = subtitles(body_segs, transcripts, fps, body_len, fixes)          # -> <Body>_Subtitles.srt
hook = subtitles(hook_segs, transcripts, fps, hook_len, fixes)          # -> <HookN>_Subtitles.srt (hook cues only)
assert not check(body) and not check(hook)
open('<Seq>_Subtitles.srt', 'w', encoding='utf-8').write(srt(hook))
rows = cue_map(body, body_segs, fps, '<Body>')                         # -> sheet: Subtitle cue map

# execute mode, only if a sequence's built length differs from the sheet:
cues, dropped = retime(rows_for_that_seq, {'03a': (120, 58), ...}, fps)  # from get_timeline_summary
assert not check(cues); open('<Seq>_Subtitles.srt', 'w', encoding='utf-8').write(srt(cues))
```

## Pitfalls

- Frame.io comment ranges are hand-dragged: they often start on the slate or end mid-chatter. Use them to choose the take, never as final cut points.
- Clip names aren't always unique, and Frame.io proxies (`_1.mp4`) may differ from the project's originals. Match by start TC + duration, and use node IDs in the build.
- Never create subclips or duplicate footage: build only from the clips the user provided (step 9.4).
- `add_to_timeline` is an insert edit. Place in timeline order from 00:00:00:00 and read back after each batch.
- Transcript word starts run early (Premiere 0.1–0.3 s, Frame.io up to 0.5 s) and soft starts can read late. Set heads and tails from `detect_silence`, keep the 3-frame head handle unless that would include the slate.
- `trim_clip` doesn't work on this Premiere build. To fix a placed clip, remove it and re-add it with corrected in/out.
- Use `get_timeline_summary` for read-backs; it's far smaller than `get_sequence_structure`, which is only for when node IDs are needed.
- Placeholder boxes on V2/V3 are overlays. Never place them with an insert on V1, and never let a V2/V3 placement ripple V1. Read back V1 after the first box.
- Long body sections: when the body runs far past the format norm, still deliver v1 as the ticket asks, and offer the cheapest tightening (cut spoken questions the text cards repeat, tighten pauses with `plan_pause_tightening`) as an open question for v2.
- The CEP bridge sometimes runs a call twice (seen with `create_sequence`, `create_bin`, `create_subclip`, `add_to_timeline_batch`, `add_to_timeline`, `import_media` and `create_caption_track`). Caption tracks can't be deleted through the bridge: check with `inspect_caption_tracks_uxp` and ask the user to delete a doubled track by hand. List the bin or read back after every create or placement, and handle any extras before going on. It can't delete project items (`delete_multiple_project_items` refuses), which is one more reason the build never creates subclips or footage copies. An extra empty sequence can go with `delete_sequence`.
- `delete_marker` removes **one** marker per call at that time, and when two markers share a start time it can take the wrong one. To remove a marker that shares its time with another, use `manage_markers_uxp` remove by GUID (needs the UXP panel). Otherwise delete at that time until the target is gone, then re-add the innocent marker with the same name, comment and duration, and check `list_markers` after each step.
- The editor may have touched the timeline between approval and a later build. Re-read the affected sequences first and work from what's there, not from the sheet.
- **Project-item in/out (`set_item_in_out`):** set the **out point first, then the in point**, in two separate calls. Setting both in one call has been refused. Pass exact source-frame times (frame × the clip's frame duration in ticks / 254016000000), not rounded seconds; for a VFR clip (e.g. iPhone 29.985 fps) use that clip's own frame grid, or the call fails. Premiere then floors the placed item to the sequence grid; that's expected.
- **Scale to Frame Size** only works on project items. To scale placed footage without touching the user's clips, use `set_clip_properties_batch` with a Motion `scale` on the track items (sequence width ÷ clip width × 100, e.g. 720→1080 = 150).
- **Writing SRTs to the edit folder without a local file tool:** `build_caption_artifact` with `approved_workspace_path` = edit folder and `output_path` writes the file, but only into a folder that already exists (it can't create folders), and the file must not exist yet. To keep pre-built cues verbatim, pass one token per cue (`text` = the whole cue) with `words_per_cue: 1`, `merge_gap_seconds: 0`, `min_cue_seconds: 0.2`, `max_cue_seconds: 15`, `max_chars_per_line: 80`. For a long multi-line placeholder cue, split the text into tokens of ≤75 characters that don't end in `.` `?` `!` (except the last), and use `words_per_cue: 12`, `max_lines: 3`; test one inline (no `output_path`) first. The `transcript_revision` field is only pattern-checked.
- **Hooks not recorded:** when the editor notes say the hooks weren't shot, each hook sequence is the Body nest at 00:00:00:00 plus a hook-only TOS placeholder (0–5 s); there are no hook subtitle files. Build Hook 1 with the nest, then duplicate it for the rest.
- **Loud locations (factories, kitchens):** `detect_silence` can return nothing even at -30 dB. Tighten from word timings and flag the heads to check by ear.
- **Frame.io comments on the first asset grabbed** sometimes miss the capture because the page already loaded them; re-grab that asset once.
