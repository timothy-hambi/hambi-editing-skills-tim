---
name: "hp-editor-agent"
description: "Rough-cut an HP/UGC ad from a Notion editor ticket + footage without Premiere: whisper transcripts, take picks, tightening, hooks + body, B-roll search across the client's Frame.io and Google Drive (Exact/Close/Placeholder), '/'-marked one-line SRT subtitles, FFmpeg render, review in the local Edit Review app, Premiere XML on approval."
---

# HP Editor Agent (native rough cut)

Use this when Tim or an editor starts a message with **HP-editor-agent**, or asks to "rough cut / edit this ticket" without Premiere, and supplies a Notion editor ticket plus footage. The footage can be a Frame.io folder, Frame.io shot links, a Drive folder or a local folder.

It does the same job as `/premiere-script-prompt` script mode, plus the build, but it **cuts in the cloud workspace with faster-whisper and FFmpeg** instead of driving Premiere:

- There is no Notion sub-page and no separate execute chat.
- Before cutting, it collects the subtitle line breaks (step 1b).
- It searches the client's Frame.io and Google Drive for B-roll before falling back to stock or placeholders, so editors don't have to supply every shot by hand (step 3b).
- It renders v1, then works through feedback rounds (v2, v3…).
- When the edit is approved, it delivers a **Premiere Pro XML** and the **subtitle SRTs**.

## Reference files

Load these on every run. A later file overrides an earlier one.

1. **House standards:** `editing-standards.md`, either the Project doc `claude/editing-standards.md` or the local copy at `D:\Hambi\03. Claude\SKILLS\editing-standards.md`. This includes its Client overrides appendix.
2. **Client rules:** `D:\Hambi\03. Claude\SKILLS\Client Rules\<Client>.md`, if the file exists. Tim adds these over time, so check the folder every run. If there's no file, use the client's Notion Brand Hub: the ticket's link first, otherwise search Notion for "<Client> Brand Hub". Never use an archived duplicate. If you find none or more than one, ask. Flag a hub marked WIP, OFFBOARDING or RE-ALIGNMENT. Read every image in it: settings screenshots give exact values, and an unticked checkbox means that setting is off.
3. **Style Library:** `D:\Hambi\03. Claude\Style Library\<Category>\`. Tim keeps adding categories and example edits (current categories: UGC Talking Head, UGC Non-talking head, Street Interview, Podcast). See step 2.
4. **The ticket:** what the ticket says wins. Flag any conflict with a client rule.

If `D:\Hambi\...` isn't reachable because the computer isn't linked, say so in one line. Then use the Project copy of the standards and carry on without the Style Library.

## Workflow

### Before anything else: Cowork check

This skill only runs in **Cowork**. It needs the desktop file tools to read the Style Library and to put the cuts into Edit Review: `device_list_dir`, `device_stage_files`, `device_commit_files` and `SendUserFile`.

Look at your own tool list before doing anything else, including the preflight.

- **All four tools are there:** you're in Cowork. Carry on to step 0.
- **Any of them is missing:** you're in a regular chat. Stop. Don't fetch the ticket, don't read Frame.io, don't pull footage and don't ask any questions about the job. Reply with only this:

  > This skill needs Cowork, because that's where I can save the cuts into Edit Review on your computer. Please open a Cowork session in the Claude desktop app, give it access to `D:\Hambi`, and send the same message there. I haven't started anything in this chat, so there's nothing to carry over.

If the editor replies in the same chat, give the same answer. A connector that can read `D:\Hambi` doesn't count, because it can't save video files there. The fallbacks further down (computer not linked, Edit Review not reachable) only apply once this check has passed.

### 0. Preflight

Report this as one short table. It's read-only, and any ❌ that blocks the job stops the run.

- **Notion:** fetch the ticket.
- **Frame.io:** run `mandatory_init` (account `eb4ebb8d-7328-4a67-b3ac-aa654a019fd1`), then read the footage folder.
- **Google Drive:** load the connector with `tool_search` ("google drive search files") and run one `search_files` for the client name. A missing connector doesn't block the run; it just means Drive B-roll falls back to a local download (step 3b).
- **Computer:** `device_list_dir` on the Style Library.
- **Disk:** `df -h` on the workspace. Note the free space; step 3b checks each download batch against it.
- **Cloud tools:** check `ffmpeg -version`, and install faster-whisper with `pip install faster-whisper --break-system-packages`.

### 1. Read the brief

- **Fetch the ticket** with `notion-fetch` (`include_file_urls: true`). Pick out:
  - the properties: Ad Type, Campaign, Concept #, Variations, Persona, Due date;
  - the concept description, the hook variations, and the script table (section, line, visual, on-screen text, and any Shot Link per row);
  - the **Editor Ticket** section, which wins over the planned script;
  - client standing notes;
  - any images on the page, which are often feedback screenshots or end cards. Download them and look at them.
- **Live script:** if an Editor Ticket or a callout changes the script, use that version, and say which one you used.
- **Pick the mode:**
  - **A. Dialogue cut:** sync speech, such as a talking head, founder, interview or podcast.
  - **B. VO cut:** a separate AI or recorded VO file is supplied and cut to footage.
  - **C. Text-led cut:** no usable speech, such as packing, ASMR or B-roll only. Script lines become on-screen text over natural sound and a music bed.
  - If the ticket expects VO but the footage has none (see step 3), stop and ask: should it be text-led, or will they supply a VO file?
- **Naming:** `[Brand]_HM_CM[#]_[AdType]_C[#]_Hook[#]` and `…_C[#]_Body`. Multi-word brands use their initials (Cornish Seaweed → CS).

### 1b. Subtitle line breaks (ask before cutting; required)

Before starting the rough cut, ask the user, whether that's Tim or another editor, to mark where each subtitle should break to the next cue, using a **"/"**.

1. **Send the script.** Put the live script lines (each hook, then the Body) in one copy-ready block, one script row per line, labelled H1, H2, B1, B2…. Example:
   `B2: First, the Super Nutrient Set, / shampoo and conditioner. / Gentle on your scalp, / and it helps your hair / feel stronger.`
2. **Ask them to add "/".** Ask them to put a "/" wherever a subtitle should cut to the next one and paste the block back. Make three points in one line each:
   - Every subtitle is **one line** unless they say otherwise for a specific cue.
   - The subtitles are delivered as **SRT files**.
   - If they'd rather not mark breaks, they can reply "default", and the house rule from `/premiere-script-prompt` applies: up to 4 words if all words are short, up to 2 if any word is 6+ letters.
3. **Run steps 2–3 while waiting.** Style loading, downloads, proxies and transcription don't depend on the breaks. Don't render until the marked script, or "default", is back.
4. **Apply the markers:**
   - Each "/"-separated chunk becomes **one cue on one line**, worded exactly as marked: their spelling, capitals, £ symbols and punctuation, except that trailing commas and full stops are dropped and ? and ! are kept, per house style.
   - A row end always ends a cue, even with no "/".
   - Line breaks inside a cue are only allowed where they asked for them (e.g. "two lines here" or a `//` inside a chunk). Otherwise never wrap.
5. **Time each cue from the transcript.** Align each chunk's words to the kept words, using fuzzy matching that tolerates mishearings and small ad-libs. A cue starts at its first word's time (snapped down to a frame). It holds until the next cue if the gap is under 0.5 s, otherwise it ends at its last word's end + 0.1 s. Minimum length is 6 frames, with no overlaps.
6. **Mismatches:**
   - A chunk with words that were never spoken (dropped in the cut, or an ad-lib) is listed under *Subtitle mismatches* in the cut sheet. Never silently drop it.
   - Spoken words that sit in no chunk are added to the nearest chunk and flagged.
7. **Check before delivery:**
   - Every cue is a single line, unless a break was requested.
   - Flag any cue over about 32 characters as a ⚠️, but don't change it, because their marks win.
   - Times increase and nothing overlaps.
   - Cue order matches the marked script.
8. **Mode C (text-led):** the "/" markers set the on-screen text cards instead. Each chunk is one card, timed to the visual beat it describes.

### 2. Load the style

1. **Pick the category.** Choose it from the ticket's Ad Type, the concept and the footage, e.g. "UGC Non-talking head" for a packing POV, or "Podcast" for a two-camera chat. Say which category you chose, and flag it if you had to pick the closest fit.
2. **Use the cached profile if it's current.** If `Style Library\<Category>\_style_profile.md` exists and is newer than every video in that folder, use it.
3. **Otherwise build or refresh it.** Stage the category's videos, at most 3 per call, and measure each one:
   - duration, cut points (`select='gt(scene,0.25)'`), average and minimum shot length, and cuts per second;
   - time to first cut and how long the hook text stays up;
   - from a contact sheet (`fps=1,scale=180:-1,drawtext=%{pts\:hms},tile=10x4`): caption position, size, box colour, highlight colour and words per line;
   - text-card style, B-roll ratio and split screens;
   - music and SFX pattern, and integrated loudness.
   Write the results to `_style_profile.md`: measured targets, patterns, and 1–2 timestamped good moments per video. Commit it with `SendUserFile`, then `device_commit_files` using the returned fileUuid.
4. **Inspo file:** a file named as the inspo in the ticket (e.g. `<Client> CM4-C18-inspo video.mp4`) is a reference **for this job only**. Never add it to the profile.
5. **Summarise the style.** Put a short "Style applied" block in the cut sheet: target shot length, caption style, hook text, music and SFX, and loudness.

### 3. Footage, proxies and transcripts

- **Frame.io folder:** `list_folder_children` results are large, so let the tool save them to a file and parse with `jq` (name, id, duration, `download_url`). Download the originals in parallel with `curl -sSL`, using each `download_url` straight away.
- **Shot links** (`/view/<id>?c=<comment>`): read the comments with `read_comments`. A comment means "use this take"; the transcript decides the exact frames.
- **Videographer take scores:** if takes are marked Best Take, Alternate or Do Not Use (in file names, Frame.io labels or comments), use Best Take first, fall back to Alternate, and never use Do Not Use. Say in the cut sheet which takes came from scores and which from transcript matching.
- **Drive:** download the main footage the same way as Drive B-roll (step 3b, point 6). A creator's personal folder lists as empty through the connector, so ask for a local download and stage it.
- **Before any download batch,** add up the file sizes and check them against `df -h`, allowing about 1.5× for proxies and WAVs. If the batch won't fit, stop and say so before downloading anything.
- **Probe each clip:** resolution, fps, rotation, colour transfer (`arib-std-b67` = HLG HDR) and audio level (`volumedetect`).
- **Proxies:** `scale=1080:1920,fps=<src>`, x264 `veryfast` at crf 16, plus a mono 16 kHz WAV per clip.
  - On 4K iPhone footage this is slow, so **run it in the background** (`nohup bash script &`) and poll. A foreground call times out at about 10 minutes.
  - Write each proxy to `*.tmp.mp4` and rename it when done.
- **Transcription:** faster-whisper `small.en`, int8, `word_timestamps=True`.
  - Load each WAV with the `wave` module into a numpy float32 array and pass the array in. Passing the file path triggers an `av` version TypeError.
  - Run it in the background and save `asr.json` incrementally.
  - If a clip's only text is "Thank you.", that's a hallucination on a silent clip. Treat it as no speech, and confirm with `volumedetect`.
- **Corrections table:** list every misheard brand word (row · heard → shown).

### 3b. B-roll search (Frame.io and Google Drive)

Run this while waiting for the 1b line breaks. It needs only the live script. The goal is to fill every B-roll beat from the client's own footage before anything goes to stock or a placeholder. Frame.io and Drive are **read-only**: never upload, comment, resolve, move or rename anything in either.

1. **List the beats.** Make one beat for:
   - every script row with a Visual or B-roll cue;
   - every talking-head stretch over about 5 s that needs breaking up (standards B5).

   For each beat, note the row, the line, what the shot must show (from the Visual column, otherwise from the line itself), and the product and variant it names (B6, B10).
2. **Search in this order** (standards B2). Stop at the first good match for each beat, but keep up to 2 candidates where the first is only Close.
   1. **The ticket:** Shot Links and B-roll links, plus their Frame.io comments.
   2. **The job's footage folder:** non-talking clips from the shoot.
   3. **The client's Frame.io library:** previous shoots and the HP library in the client's Frame.io project. Find the project with the Frame.io connector, list its folders with `list_folder_children` (save to disk, parse with `jq`), and match beat keywords against file names, folder names, labels and comments. If the connector has a search tool, search by keyword first and browse second. Look at a frame from each candidate before proposing it.
   4. **The client's Google Drive:** use `search_files` with the client name plus beat keywords, limited to video and image MIME types, across shared drives and Shared with me. Start from any Drive links in the Brand Hub or ticket. Get size and duration with `get_file_metadata`.
   5. **Approved UGC:** clips in Frame.io or Drive folders marked approved or delivered.
   6. **Stock:** UGC or iPhone-style only (Pexels, Envato, Motion Array), never glossy commercial footage. Give search terms and 1–2 candidate links. Claude can download free Pexels clips after approval; Envato and Motion Array clips are downloaded by the editor, because the licences are theirs.
   7. **AI:** this skill never generates AI footage. Leave a placeholder with a ready-to-use prompt in the cut sheet.
3. **Check every candidate before proposing it.** Reject old packaging, the wrong variant, glossy-looking stock and anything that looks AI (B3, B6). Compare the packaging with the Brand Hub's current pack shots.
4. **Label each beat:**
   - **Exact:** shows what the line says, with the right product and variant.
   - **Close:** the right product or subject, but not the exact action or setting. Say what's different.
   - **Placeholder:** nothing suitable found. It becomes a labelled box in the rough cut (step 4).
5. **Ask for approval in one table** in chat: # · Row · Line · Beat · Pick · Source (Frame.io / Drive / folder / stock, with link or path) · In–out · Label · Size. End with the total download size and the number of Placeholders. The editor can approve with edits, e.g. "approve all, swap 4 for the second option, drop 7". Approving the table is permission to download those files and no others. Download nothing before it.
6. **Download the approved batch** after the space check in step 3.
   - **Frame.io:** `curl -sSL` each `download_url` straight away, in parallel.
   - **Drive:** use the connector's `download_file_content` for files up to about 20 MB (stills, short clips), and decode the base64 to disk.
   - **Drive files that are larger, unreachable or in a creator's personal folder:** list them with their sizes and ask the editor to download them into the job's footage folder on their computer, then stage them with `device_stage_files`.
   - **If the owner has turned off downloads,** stop and say so. Never work around it.
   - Make proxies for B-roll the same way as for footage. Only transcribe B-roll that has speech.
7. **Record each pick in `spec.json`** with its source link, its label and the original's location, so step 9 can point the XML at it.

### 4. Pick takes, tighten and structure

Read `premiere-script-prompt/SKILL.md` (glob `**/premiere-script-prompt/SKILL.md`) and follow:

- **Step 3:** take choice, in/out points, 3-frame head and 5-frame tail.
- **Step 3b:** tightening. Cut intros, fillers, stutters, and pauses over 0.3 s down to about 0.14 s, using the 10 ms dB envelope with the kept-word guard. Verify that no kept word is lost.
- **Step 4:** structure. One **Body**, plus one sequence per hook that plays the hook segments followed by the Body.

Copy its **Timecode helper** into the scratchpad. Use its **Subtitle helper** for word timing and SRT writing only. The cue boundaries come from the "/" markers (step 1b), and its 4/2-word chunking is used only when the user replied "default".

- **Mode C:** script chunks become timed cards paced to the style profile's shot length. Use counters or value stacks wherever the concept is about counting (e.g. a running "VALUE IN BOX £"). Ask before using any number the ticket leaves unconfirmed, such as gift values.
- **B-roll and graphics, pass 1:**
  - Place the approved Exact and Close picks from step 3b on the word that names them (P6), on V2 above the A-roll. The A-roll is never replaced.
  - Everything else is a **placeholder**: a labelled box burned into the rough cut (`[BROLL] P03 — description`) plus a row in the cut sheet.
- **Alternates:** strong off-script moments (a better ad-lib, a natural reaction) go in the cut sheet's Alternates list with source and in–out, never into the cut.

### 5. spec.json (single source of truth)

All edit decisions live in `spec.json`, in the same format as `ugc-revision`:

- **Sources:** proxy path, device path, frame count.
- **Card and caption style:** from the client rules and the style profile.
- **Cards.**
- **Sequences:** for the Body and each hook:
  - segments (`src`, `in`, `out`, and `speed` or `fill`; no freeze-frame holds, slow the clip instead);
  - overlays, including B-roll picks with their label (Exact or Close), source link and original's location;
  - placeholders;
  - subtitle cues (start, end, text, row);
  - notes.
- **Audio:** dialogue, plus the music bed's file and level under speech.

The renderer, the SRT writer and the XML builder all read only `spec.json`.

### 6. Render v1

Render the **Body first**, then each hook (hook segments + Body via concat).

**Picture**

- Split before trimming the same input more than once.
- Per segment: `trim` → `setpts` → `fps`. Join with `concat`, then add 0.2 s of `tpad`.
- HLG footage is tone-mapped to SDR:
  `zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p`
- Cards are Pillow PNGs, overlaid with `enable='between(t,a,b)'`.
- Subtitles are **burned into the review MP4 only**, from the same cues as the SRT, so reviewers see them in place. They stay one line, styled per the client rules and the style profile. The SRT is the deliverable.
- Use the brand font if supplied. Otherwise use DM Sans from jsDelivr `@fontsource/dm-sans` (GitHub raw is blocked) and flag it.

**Audio**

- Dialogue: `loudnorm=I=-14:TP=-1:LRA=11` then `volume=-1.5dB`.
- Music: duck under speech (`sidechaincompress`, or about −20 dB).
- Verify with `ebur128`.

**Encode:** x264 crf 18, bt709 tags, AAC 192k, `+faststart`, 1080×1920. Render **one sequence at a time**, because running renders in parallel runs out of memory.

**QC**

- Duration matches the spec within 0.1 s.
- Loudness is −14 ±0.5 LUFS.
- Check a frame strip at every cut, card and hook→body join.
- No kept word is lost.
- Subtitles are one line, inside the safe zone, and don't cover the product or faces.
- Run the `editing-standards.md` pre-export checklist.

### 7. Deliver each version

Put these in `/mnt/user-data/outputs/<Seq base>/`:

- `<Seq>_v<N>.mp4` for each hook (the Body only on request);
- `<Seq>_Subtitles_v<N>.srt` for the Body and each hook. Hook SRTs hold only that hook's cues; the Body's cues live in the Body SRT, the same as `/premiere-script-prompt` step 5b;
- `<Seq base>_CutSheet_v<N>.md`. It covers: the header (ticket, mode, category, style applied, script used); client notes; sources and transcript source; a table of # · Seq · Section · Line (heard) · Src · Source in–out · Timeline in–out; the B-roll table from step 3b with each beat's label and source; placeholders, with an AI prompt or stock search terms for each; corrections; subtitle mismatches; a subtitle preview; alternates; checks; and open questions.

Then upload them to **Edit Review**, the local Frame.io-style review app. Don't post the MP4s in chat.

**Edit Review folder:** `D:\Hambi\03. Claude\Edit Review\`. The app is `review.html`, which opens in Chrome or Edge with no install. Its layout is described in `README.md` in that folder.

1. **Job folder.** Each job lives in `jobs\<Seq base>\`, e.g. `jobs\CS_HM_CM4_UGC_C18\`. On v1, create `job.json`:
   ```json
   {"code":"<Seq base>","title":"<Brand> · C<#> <Concept>","client":"<Brand>","ticket":"<Notion URL>","updated":"<ISO now>",
    "sequences":[{"id":"H1","label":"Hook 1","versions":[{"v":1,"file":"v1/<Seq>_v1.mp4","srt":"v1/<Seq>_Subtitles_v1.srt","created":"<date>"}]}, …, {"id":"BODY","label":"Body",…}]}
   ```
   On later versions, stage the current `job.json` first (`device_stage_files`). Append each new version to every sequence's `versions`, bump `updated`, and write it back. Never overwrite the user's `notes.json` or `status.json`.
2. **Upload.** `SendUserFile` each MP4 and SRT (`display: attach`) to get fileUuids. Then `device_commit_files` them into `jobs\<Seq base>\v<N>\`, and commit `job.json` (stagedPath works for files written with Write). Also commit the cut sheet into `v<N>\`. The Body MP4 goes up too, so reviewers can note it directly.
3. **Message the app.** Append to `agent.json` `messages` (`{at, version, text}`), e.g. "v1 uploaded: 3 hooks + body, 0:48 avg". It shows on the job's status line.
4. **Chat.** Write 3–5 lines: "v<N> is in Edit Review", the job code, runtime per hook, style applied, ⚠️ items and open questions. Ask the user to leave timestamped notes in Edit Review, then click **Notes done → revise** or **Approve v<N>**.

**If Edit Review isn't reachable** (the computer isn't linked), fall back to `SendUserFile` with `display: render` in chat, and say so.

### 8. Feedback rounds

**Trigger.** A round starts when the user pastes the message the app copies, `HP-editor-agent: notes done for <CODE> v<N> …`, or just says the notes are in.

**Read the notes.** Stage `jobs\<CODE>\notes.json` and `status.json`.

- Act on every note with `state` `open` whose version is the latest. Notes have `seq` (H1/H2/H3/BODY), `version`, `t` (seconds into that cut) and `text`.
- Map `t` to a spec row through the sequence's segment table.
- A note on a hook at a time inside the Body part is a Body note, so it applies to every hook. Say so.
- If `status.json` isn't `notes_submitted` for the latest version, confirm with the user before revising, because they may still be adding notes.

**Reply to every note.** Write `agent.json` `notes[<id>] = {state: "done" | "dismissed", reply: "<one line on what changed, or why not>", version: <N+1>, at: <ISO>}`.

- Use `dismissed` only with a reason, e.g. the note conflicts with the ticket or client rules.
- Commit `agent.json` together with the v<N+1> files so replies and the new version land together.

**Then:**

- Each note becomes a `spec.json` change, and the version number goes up.
- Re-render only the sequences that changed. A Body change means every hook changes.
- Regenerate the SRTs for any sequence whose timing or wording changed.
- QC, then upload v<N+1> to Edit Review (step 7). The app shows a "v<N+1> is ready" banner and Claude's reply under each note.

After each round, sort the notes:

- **All clients:** offer to add them to `editing-standards.md`.
- **This client only:** offer to add them to `Client Rules\<Client>.md`, creating it if needed.
- **Tim's own style:** offer to add them to the category's `_style_profile.md`.

Don't write any of these without an OK.

### 9. Approval → Premiere Pro XML + SRTs

When the edit is approved, deliver the Premiere hand-off. Approval is any of:

- the app's copied message, `HP-editor-agent: APPROVED <CODE> v<N> …`;
- `status.json` showing `{state: "approved", version: N}`;
- a chat "approved", "signed off" or "no more notes".

First stage `status.json` and check that the approved version is the latest. If notes are still open, list them and ask whether to ignore them.

**1. XML:** one file, `<Seq base>_ALL_v<N>.xml`, in FCP7 xmeml v4.

- Structure: `<project><bin>` holding the Body sequence and one sequence per hook. Each hook places the Body sequence as a nested clipitem after its hook segments. If nesting fails to import, flatten the Body segments into each hook and note it.
- Declare each file in full once; reuse it after that as `<file id="…"/>`.
- `pathurl` is `file://localhost/D%3a/<quoted path>`, pointing at the **original** footage on the user's machine, not the proxies. If the originals only exist in Frame.io, ask where they're kept locally. For B-roll pulled from Frame.io or Drive in step 3b, commit the originals into `delivery\<CODE>\broll\` and point the `pathurl`s there; if those files add up to more than about 2 GB, ask first whether the editor already has them locally.
- 4K portrait sources get Basic Motion scale 50% (3840→1920). Check this on the first import.
- Tracks:
  - V1: the cut, with speed changes as a `timeremap` speed %;
  - V2: placeholders and B-roll;
  - V3: card PNGs as `stillframe`;
  - A1: dialogue;
  - A2: music.
- Markers at frame 0 covering the grade, loudness, card editability and any approximations.

**2. Final SRTs** for the Body and each hook, from the approved cues. Import them in Premiere as caption tracks (File → Import, then drag to the sequence). The one-line rule and the "/" breaks are preserved.

**3. Card PNGs**, committed to `…\Premiere\cards\`.

**Validate the XML:** it parses, ids are unique, each file is defined once, the sequence count is right, and the SRTs pass the one-line check.

**Deliver:** `SendUserFile` (`attach`), then `device_commit_files` into `D:\Hambi\03. Claude\Edit Review\delivery\<CODE>\`:

- the XML and SRTs at the top level;
- the card PNGs in `cards\`.

Set `pathurl`s to that card folder. Append an `agent.json` message: "Approved v<N> delivered: XML, SRTs, cards in delivery\<CODE>". Offer to test-import through the Premiere MCP if Premiere is open.

## Pitfalls

- The Frame.io audit log errors on this account; don't use it.
- Folder listings can run past 70k characters. Let the tool save them to disk and parse with `jq`.
- A creator's Google Drive folder lists as empty through the connector. Ask for a local download.
- Drive downloads through the connector come back as base64 in the reply, so keep them to small files (about 20 MB). Anything bigger goes to the editor as a local download.
- Never pass a beat off as Exact when it's only Close. A Close pick with a clear note beats a reviewer finding the gap.
- For 4K HEVC iPhone clips, decode and transcode in the background. The cloud has 2 CPUs and 7 GB RAM.
- Script-made files can't be committed via `stagedPath` (HTTP 400). Always use `SendUserFile` → fileUuid → `device_commit_files`.
- Never invent prices, gift values or claims. When a ticket says "confirm on the day", ask.
- If the creator didn't record the scripted VO, say so before building and offer text-led or a supplied VO.
- Never re-break subtitles the user marked with "/". Flag long cues instead of changing them.
- Edit Review can't wake this chat: its buttons save `status.json` and copy a ready-to-paste message. Always read `status.json` and `notes.json` fresh (stage them again) at the start of each round. Never trust an earlier copy, because the user may have added notes since.