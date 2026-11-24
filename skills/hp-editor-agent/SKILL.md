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
- It logs each stage's workload and usage to the HP Editor Usage Log in Notion, with a local CSV copy, so the cost of a run can be measured on the Team plan (step 10).

## Reference files

Load these on every run. A later file overrides an earlier one, so a client's rules beat the Style Library and the ticket beats everything.

1. **House standards:** `standards/editing-standards.md` (synced into the Project; local clone `D:\Hambi\03. Claude\hambi-editing-skills-tim\hambi-editing-skills-tim\standards\editing-standards.md`). This includes its Client overrides appendix.
2. **Style Library:** `D:\Hambi\03. Claude\Style Library\<Category>\`. Tim keeps adding categories and example edits (current categories: UGC Talking Head, UGC Non-talking head, Street Interview, Podcast). See step 2.
3. **Client rules:** read both of these on every run.
   - **Client guide:** `brand-hubs/<client>.md` in the repo (lowercase, hyphenated; local clone `D:\Hambi\03. Claude\hambi-editing-skills-tim\hambi-editing-skills-tim\brand-hubs\`), if it exists. Tim adds these over time, so check the folder every run.
   - **Brand Hub:** the client's Notion Brand Hub, from the ticket's link first, otherwise by searching Notion for "<Client> Brand Hub". Never use an archived duplicate. Flag a hub marked WIP, OFFBOARDING or RE-ALIGNMENT. Read every image in it: settings screenshots give exact values, and an unticked checkbox means that setting is off.
   - **If the two disagree,** follow the client guide and list the conflict under open questions in the cut sheet, so Tim can bring them back in line. The Brand Hub fills in everything the file doesn't cover, such as the current CTA, end card and pack shots.
   - **If a source is missing:** with a client guide but no Brand Hub, carry on with the guide and say so. With more than one Brand Hub, ask which to use. With neither a file nor a hub, ask.
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

### Resume check (before the preflight)

A job's edit decisions are saved on the user's computer after every version (step 7), so a job can be picked up in a new session.

1. Work out the job code from the message (`HP-editor-agent: notes done for <CODE> v<N>`, `APPROVED <CODE> v<N>`) or from the ticket's naming (step 1).
2. Run `device_list_dir` on `D:\Hambi\03. Claude\Edit Review\jobs\<Seq base>\`.
3. **If the folder has a `work\spec.json`:** this is a job in progress. Don't start again from step 1.
   - Stage `job.json`, `work\spec.json`, `work\asr.json`, `work\usage.json` (if it exists), `notes.json` and `status.json`.
   - Add 1 to `sessions` in `usage.json` (step 10).
   - Say in one line which version you're resuming from.
   - Rebuild proxies only for the sources the sequences being re-rendered use, from the source links recorded in `spec.json`. Don't transcribe again; `asr.json` already has the word timings.
   - Carry on at step 8 (feedback) or step 9 (approval).
4. **If the folder doesn't exist or has no `work\spec.json`:** it's a new job. Carry on to the preflight.
5. If the user wants a fresh start on an existing job, they have to say so. Never overwrite a saved `spec.json` with a new v1 without asking.

### 0. Preflight

Report this as one short table. It's read-only, and any ❌ that blocks the job stops the run.

- **Notion:** fetch the ticket.
- **Frame.io:** run `mandatory_init` (account `eb4ebb8d-7328-4a67-b3ac-aa654a019fd1`), then read the footage folder.
- **Google Drive:** load the connector with `tool_search` ("google drive search files") and run one `search_files` for the client name. A missing connector doesn't block the run; it just means Drive B-roll falls back to a local download (step 3b).
- **Computer:** `device_list_dir` on the Style Library.
- **Disk:** `df -h` on the workspace. Note the free space; step 3b checks each download batch against it.
- **Cloud tools:** check `ffmpeg -version`, and install faster-whisper with `pip install faster-whisper --break-system-packages`.
- **Usage baseline:** start the stage clock and ask for the before readings, as in step 10. This doesn't go in the table and doesn't block the run.

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
   - Each "/"-separated chunk becomes **one cue on one line**, worded exactly as marked: their spelling, capitals, £ symbols and punctuation. Follow sentence grammar (standards C8): keep full stops, commas, ? and ! at the end of a cue, and start the cue that opens a new sentence with a capital.
   - Where the punctuation comes from:
     - **Line said word for word from the script:** the script's punctuation and capitals.
     - **Line changed on the shoot** (words added, dropped or reworded): the cue text follows what was actually said, with standard English grammar. List these lines in the cut sheet under *What she/he says vs the ticket*.
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
- **Proxies:** 1080×1920 at the source frame rate, x264 `veryfast` at crf 16, plus a mono 16 kHz WAV per clip. Never stretch a clip to fit:
  - **Check which way up every clip is first** (see the orientation check below), and fit the clip only after it's upright. A portrait clip that was saved on its side is rotated, not cropped.
  - **Already 9:16:** `scale=1080:1920,fps=<src>`.
  - **Any other shape** (landscape, square, 4:5): fill the frame and centre-crop with `scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=<src>`.
  - Look at a frame from every cropped clip. If the crop cuts off the subject or the product, shift the crop (`crop=1080:1920:x:y`) or ask the editor how they want it framed.
  - Record each cropped clip's original size and crop offset in `spec.json`, and list them in the cut sheet under ⚠️ so the framing gets checked.
  - On 4K iPhone footage this is slow, so **run it in the background** (`nohup bash script &`) and poll. A foreground call times out at about 10 minutes.
  - Write each proxy to `*.tmp.mp4` and rename it when done.
- **Orientation check** (every clip, before its proxy is made): FFmpeg already applies a clip's rotation flag, so this is for clips where the flag is missing or wrong and the picture comes out sideways or upside down.
  1. Pull one frame from the middle of each clip, as FFmpeg displays it.
  2. **Use faces as the reference.** Run a face detector (OpenCV, `pip install opencv-python-headless --break-system-packages`) on the frame at 0°, 90°, 180° and 270°. The rotation where a face is found the right way up is the upright one. If the first frame has no face, try two more frames from the clip.
  3. **No face in the clip** (product, packing or hands-only shots): look at the frame yourself and judge from on-pack text, the horizon, and which way things rest or pour.
  4. **Still not sure, or the detector finds faces at two rotations:** leave the clip as it is and ask the editor. Never guess a rotation.
  5. Rotate with `transpose=1` (90° clockwise), `transpose=2` (90° anticlockwise) or `hflip,vflip` (180°), placed before the scale in the proxy filter.
  6. Record the rotation for each clip in `spec.json`, and list every rotated clip in the cut sheet under ⚠️ with a before and after frame, so the editor can confirm it.
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
- **Hook text overlay** (standards H1): every hook gets a text overlay at the top that works with the sound off.
  - Use the hook's on-screen text from the ticket, worded exactly as written.
  - If the ticket gives none, burn in a placeholder card (`[HOOK TEXT] H2`) and suggest wording under open questions in the cut sheet. Never put unapproved copy into the cut as if it were final.
- **CTA and end card** (standards E1 to E4): the Body ends on the client's current end card.
  - Find it in this order: the ticket, the client guide, the Brand Hub. Pick the version for the product and offer this ticket is about.
  - Download it and place it after the final line, as its own segment. Captions stop before it unless the client rules say otherwise.
  - Offer text, prices and roundels must match the ticket exactly. If the end card shows a different offer, flag it and don't use it.
  - If there is no end card, or there are several and it isn't clear which is current, burn in a placeholder (`[END CARD] — <product / offer>`) and ask. Never build an end card from scratch.
- **Music** (standards A1): this skill doesn't choose or license music by itself.
  - Use a track only if the ticket names one or the editor supplies a file, and check it against the client rules (some brands want soft music, or no SFX).
  - Otherwise render with dialogue only and add a **music brief for Artlist** to the cut sheet, so the editor can find a track quickly:
    - the mood from the brief and the client rules (e.g. soft and calm, upbeat, no orchestral);
    - 2 or 3 sets of Artlist search terms to try: genre, mood, instruments, and whether it should have vocals;
    - a tempo range and energy level that fit the cut's pacing in the style profile;
    - the length needed, and where the track should lift or drop (hook, product reveal, CTA);
    - any approved concept of the client's whose track would suit, as a reference.
  - Suggest search terms only. Never name a specific Artlist track or link, because Claude can't search or play the Artlist library and a guessed title may not exist.
  - The editor downloads the track from Artlist, since the licence is theirs, and supplies the file. Add it in the next round at the level under speech set in step 6.
  - Say in the chat summary whether the cut has music or is waiting for a track.
- **Alternates:** strong off-script moments (a better ad-lib, a natural reaction) go in the cut sheet's Alternates list with source and in–out, never into the cut.

### 5. spec.json (single source of truth)

All edit decisions live in `spec.json`, in the same format as `ugc-revision`:

- **Sources:** proxy path, device path, frame count, the source link (Frame.io or Drive) so the clip can be fetched again, any rotation applied, and for a cropped clip its original size and crop offset.
- **Card and caption style:** from the client rules and the style profile.
- **Cards:** text cards, each hook's text overlay and the end card, each marked as final or placeholder.
- **Sequences:** for the Body and each hook:
  - segments (`src`, `in`, `out`, and `speed` or `fill`; no freeze-frame holds, slow the clip instead);
  - overlays, including B-roll picks with their label (Exact or Close), source link and original's location;
  - placeholders;
  - subtitle cues (start, end, text, row);
  - notes.
- **Audio:** dialogue, plus the music bed's file and level under speech, or a note that the cut is waiting for a track.

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
- `<Seq base>_CutSheet_v<N>.md`. It covers: the header (ticket, mode, category, style applied, script used); client notes; sources and transcript source; a table of # · Seq · Section · Line (heard) · Src · Source in–out · Timeline in–out; the B-roll table from step 3b with each beat's label and source; placeholders, with an AI prompt or stock search terms for each; the hook text, end card and music status (final, placeholder or waiting); corrections; subtitle mismatches; a subtitle preview; alternates; checks; and open questions.

Then upload them to **Edit Review**, the local Frame.io-style review app. Don't post the MP4s in chat.

**Edit Review folder:** `D:\Hambi\03. Claude\Edit Review\`. The app is `review.html`, which opens in Chrome or Edge with no install. Its layout is described in `README.md` in that folder.

1. **Job folder.** Each job lives in `jobs\<Seq base>\`, e.g. `jobs\CS_HM_CM4_UGC_C18\`. On v1, create `job.json`:
   ```json
   {"code":"<Seq base>","title":"<Brand> · C<#> <Concept>","client":"<Brand>","ticket":"<Notion URL>","updated":"<ISO now>",
    "sequences":[{"id":"H1","label":"Hook 1","versions":[{"v":1,"file":"v1/<Seq>_v1.mp4","srt":"v1/<Seq>_Subtitles_v1.srt","created":"<date>"}]}, …, {"id":"BODY","label":"Body",…}]}
   ```
   On later versions, stage the current `job.json` first (`device_stage_files`). Append each new version to every sequence's `versions`, bump `updated`, and write it back. Never overwrite the user's `notes.json` or `status.json`.
2. **Upload.** `SendUserFile` each MP4 and SRT (`display: attach`) to get fileUuids. Then `device_commit_files` them into `jobs\<Seq base>\v<N>\`, and commit `job.json` (stagedPath works for files written with Write). Also commit the cut sheet into `v<N>\`. The Body MP4 goes up too, so reviewers can note it directly.
3. **Save the working files.** After every version, commit these into `jobs\<Seq base>\work\` with `SendUserFile` → fileUuid → `device_commit_files`:
   - `spec.json`, the current edit decisions;
   - `spec_v<N>.json`, a copy kept for each version so a round can be rolled back;
   - `asr.json`, the word-level transcripts, and the corrections table;
   - `usage.json`, the usage counters for the stage in progress (step 10).

   Without these, a feedback round in a new session would have to start from nothing. Proxies aren't saved, because they can be rebuilt from the source links in `spec.json`.
4. **Message the app.** Append to `agent.json` `messages` (`{at, version, text}`), e.g. "v1 uploaded: 3 hooks + body, 0:48 avg". It shows on the job's status line.
5. **Chat.** Write 3–5 lines: "v<N> is in Edit Review", the job code, runtime per hook, style applied, ⚠️ items and open questions. Ask the user to leave timestamped notes in Edit Review, then click **Notes done → revise** or **Approve v<N>**.
6. **Usage row.** On v1, write the `v1` usage row (step 10) and put the after-readings question in this summary.

**If Edit Review isn't reachable** (the computer isn't linked), fall back to `SendUserFile` with `display: render` in chat, and say so.

### 8. Feedback rounds

**Trigger.** A round starts when the user pastes the message the app copies, `HP-editor-agent: notes done for <CODE> v<N> …`, or just says the notes are in.

**Check the workspace first.** If `spec.json` isn't in the workspace (a new session, or the workspace was reset), follow the Resume check near the top before doing anything else.

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
- **This client only:** offer to add them to `brand-hubs/<client>.md` in the repo, creating it if needed.
- **Tim's own style:** offer to add them to the category's `_style_profile.md`.

Don't write any of these without an OK.

Then write the round's usage row (step 10). Ask for the next round's before readings when the next notes arrive.

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
- A source that was rotated or cropped for the proxy gets the Basic Motion rotation, scale and position that reproduce what's recorded in `spec.json`. Add a marker naming those clips so the editor checks the framing.
- Tracks:
  - V1: the cut, with speed changes as a `timeremap` speed %;
  - V2: placeholders and B-roll;
  - V3: card PNGs, hook text overlays and the end card as `stillframe`;
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

Then write the approval usage row (step 10).

### 10. Usage log

The Team plan has no per-skill or per-member usage view, so this log is how Tim measures what a run costs. Claude can't see tokens, limits or spend, so the log records the workload Claude can count, plus the usage readings the user gives. **Logging never blocks, delays or replaces a delivery.**

**Stages.** Write one row per stage, holding only that stage's numbers, so a job's total is the sum of its rows:

- `v1`: preflight to v1 in Edit Review (step 7);
- `round`: one feedback round, notes to v<N+1> (step 8);
- `approval`: the Premiere hand-off (step 9);
- `stopped`: the run ended early after work had started (a blocking ❌ after downloads, the user abandons the job, an unrecoverable error). Say why in `notes`.

The Cowork-check refusal logs nothing, because nothing ran.

**Start of a stage**

1. Record `started` with `date -u +%FT%TZ`.
2. Ask for the before readings in one line, then carry on without waiting:
   > Before I start: what do your **current session** and **weekly** usage show on the Usage page in Settings? Reply like `12 / 40`, or `skip`.
3. Start a fresh `stage` block in `work\usage.json` with every counter at 0. On a resumed job, keep the job's earlier rows untouched.

**Counters (kept in `usage.json` as you go)**

- `footage_clips`, `footage_min`: clips downloaded for the cut and their total minutes;
- `download_gb`: everything downloaded, footage and B-roll;
- `transcribed_min`: minutes run through faster-whisper;
- `broll_beats`, `broll_exact`, `broll_close`, `broll_placeholder`, `broll_candidates_checked`;
- `sequences_rendered`: sequences delivered this stage;
- `render_passes`: every FFmpeg render, including QC re-renders;
- `output_min`: total minutes of the delivered MP4s;
- `notes_actioned`: notes marked done or dismissed;
- `tool_calls_approx`: Claude's own count of tool calls this stage (label it approximate);
- `sessions`: 1, plus 1 each time the Resume check picks the job up in a new session.

**End of a stage**

1. Record `ended` and work out `wall_min`.
2. Ask for the after readings in the closing chat summary, in one line: "For the usage log: what do session and weekly show now?"
3. **Write the row to both places, local first,** so the editor always keeps a copy even if Notion fails.
   1. **Local CSV:** `D:\Hambi\03. Claude\Edit Review\usage-log.csv` on the editor's computer.
      - Stage it with `device_stage_files`. If it doesn't exist, create it with the header below.
      - Append the row with `notion_url` blank, then commit with `SendUserFile` → fileUuid → `device_commit_files`, the same as the other script-made files.
      - Never edit or reorder other rows. The only rows you may change are this stage's own (after readings) and blank `notion_url`s (point 4 below).
   2. **Notion:** create a page in the **HP Editor Usage Log** database with `notion-create-pages`, parent `data_source_id` `42211884-e3c9-8199-90c2-000b878f1bf8` (database: https://app.notion.com/p/42211884e3c9814990ffcc9c7f80f1c0, on the HP Editor Skill Usage page).
      - Fill the properties from the same row, using the mapping below. Use `allow_async: false`, so the page URL comes back straight away.
      - Write the returned page URL into the row's `notion_url` and commit the CSV again.
   3. **If the Notion write fails,** don't retry in a loop and don't hold up the delivery. Leave `notion_url` blank, say in one line that the row is saved locally and will sync next time, and carry on.
4. **Sync pending rows.** At the start of every stage, and before a usage summary, check the local CSV for rows with a blank `notion_url`. Create a Notion page for each, then fill in its `notion_url`. Before creating one, search the database for a page with the same Run title and Started time, so a row that reached Notion without its URL being saved isn't added twice.
5. **When the after readings arrive** (a reply, or in the same message as the next stage's notes or approval):
   - Fill them in on the CSV row, recompute the deltas and commit.
   - Update the same Notion page (from `notion_url`) with `notion-update-page`: the four readings, both deltas, and Notes if a reset was flagged. If the row has no `notion_url` yet, point 4 will carry the readings across when it syncs.
   - If the readings never arrive, leave them blank in both places. Never estimate a reading.

**Columns**

```
logged_at,job,client,ticket,editor,ad_type,mode,category,stage,version,started,ended,wall_min,sessions,footage_clips,footage_min,download_gb,transcribed_min,broll_beats,broll_exact,broll_close,broll_placeholder,broll_candidates_checked,sequences_rendered,render_passes,output_min,notes_actioned,tool_calls_approx,session_before,session_after,session_delta,weekly_before,weekly_after,weekly_delta,notes,notion_url
```

**Notion property mapping.** Number properties take numbers; leave a property out when its value is blank.

| CSV column | Notion property |
|---|---|
| (job + stage) | **Run** (title): `<job> · <stage>`, or `<job> · round v<N>` for a round |
| job, client, editor, ad_type, notes | Job, Client, Editor, Ad Type, Notes |
| ticket | Ticket |
| mode | Mode: `A Dialogue`, `B VO` or `C Text-led` |
| category | Category (select; a new Style Library category is added as a new option) |
| stage, version | Stage, Version |
| started, ended | `date:Started:start`, `date:Ended:start`, each with `is_datetime` 1 |
| wall_min, sessions | Wall min, Sessions |
| footage_clips, footage_min, download_gb, transcribed_min | Footage clips, Footage min, Download GB, Transcribed min |
| broll_beats, broll_exact, broll_close, broll_placeholder, broll_candidates_checked | B-roll beats, B-roll exact, B-roll close, B-roll placeholder, B-roll candidates checked |
| sequences_rendered, render_passes, output_min, notes_actioned, tool_calls_approx | Sequences rendered, Render passes, Output min, Notes actioned, Tool calls (approx) |
| session_before, session_after, session_delta | Session before %, Session after %, Session delta % |
| weekly_before, weekly_after, weekly_delta | Weekly before %, Weekly after %, Weekly delta % |

`logged_at` and `notion_url` stay in the CSV only. Notion sets **Logged** and **Run ID** itself.

- `editor`: the editor named on the ticket; otherwise the person running the job if they've said who they are; otherwise blank.
- `mode`: A, B or C (step 1). `category`: the Style Library category (step 2).
- **Deltas:** after minus before. If an after reading is lower than its before, the limit reset during the stage: leave that delta blank and put `session reset` or `weekly reset` in `notes`.
- `notes`: anything that skews the numbers, e.g. a style profile rebuild, a resumed session that re-made proxies, a long wait for the line breaks, or other Claude work done during the stage.

**If the computer isn't linked** (no local CSV), still write the Notion page, and also put the row in chat as one CSV line in a code block, so the editor can paste it into their local log.

**Usage summary.** When Tim asks for a usage summary or report, sync any pending rows first (point 4), then read the Notion database, which holds every editor's runs. If Notion isn't reachable, use the local CSV and say it covers this computer only. Report in a few lines or a small table:

- the average session and weekly delta per stage, and per finished job (v1 + rounds + approval);
- the same split by mode, category and client, once there are at least 3 jobs in a group;
- which counters move with the deltas (e.g. transcribed minutes or render passes), as the likely cost drivers;
- how many rows have no readings, since those can't be counted.

With fewer than about 10 rows that have readings, say the numbers are early and may move.

## Pitfalls

- The Frame.io audit log errors on this account; don't use it.
- Folder listings can run past 70k characters. Let the tool save them to disk and parse with `jq`.
- A creator's Google Drive folder lists as empty through the connector. Ask for a local download.
- Drive downloads through the connector come back as base64 in the reply, so keep them to small files (about 20 MB). Anything bigger goes to the editor as a local download.
- Never pass a beat off as Exact when it's only Close. A Close pick with a clear note beats a reviewer finding the gap.
- For 4K HEVC iPhone clips, decode and transcode in the background. The cloud has 2 CPUs and 7 GB RAM.
- Script-made files can't be committed via `stagedPath` (HTTP 400). Always use `SendUserFile` → fileUuid → `device_commit_files`.
- Never rely on the workspace surviving between rounds. `spec.json` and `asr.json` on the user's computer are the saved state (step 7).
- Never invent prices, gift values or claims. When a ticket says "confirm on the day", ask.
- If the creator didn't record the scripted VO, say so before building and offer text-led or a supplied VO.
- Never re-break subtitles the user marked with "/". Flag long cues instead of changing them.
- The usage log is written locally first, then to Notion. A Notion failure never loses a row: the CSV keeps it and step 10 syncs it next time.
- Never estimate or invent a usage reading. A blank reading is fine; a guessed one spoils the benchmark.
- Edit Review can't wake this chat: its buttons save `status.json` and copy a ready-to-paste message. Always read `status.json` and `notes.json` fresh (stage them again) at the start of each round. Never trust an earlier copy, because the user may have added notes since.