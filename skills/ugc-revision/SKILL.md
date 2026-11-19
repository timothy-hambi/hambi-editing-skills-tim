---
name: "ugc-revision"
description: "Action client/internal Frame.io feedback on a creator's UGC ad (all hooks) without Premiere: Notion ticket → cut sheet → approval → FFmpeg render → feedback loops → single Premiere XML."
---

# UGC Revision (native edit)

Use this when Tim or an editor shares a Notion editor ticket (or Frame.io link) for a UGC ad and asks to "action the comments", "revise the creator edit", "do the amends", or similar. The deliverables are revised MP4s for every hook. Once the user signs off a version, you also produce **one** Premiere XML holding every hook.

The edit is done in the cloud workspace with FFmpeg and Python. Premiere isn't needed until the XML handoff.

## Non-negotiables

1. **Approval gate.** Never render before the user approves a cut sheet. Never export the XML before the user says the edit is final ("approved, no more notes").
2. **One source of truth.** All edit decisions live in `spec.json`. The renderer and the XML builder both read it, so the MP4 and the XML can't drift apart.
3. **House standards.** Read `editing-standards.md` before planning. It lives in the Project as `claude/editing-standards.md` and locally at `D:\Hambi\03. Claude\SKILLS\editing-standards.md`. Run its pre-export checklist on every render.
4. **Brand rules.** Pull fonts, colours, offer wording and banned visuals from the client's Brand Hub and the Client overrides in `editing-standards.md`. If a brand font file isn't available, ask once. If none is supplied, use the agreed stand-in and flag it.
5. **Ticket overrides.** Ticket instructions beat client comments. For example, "ignore the hat/table comment" means you keep those.
6. **Version every round.** Use `vN` in every filename, put each round's exports in their own `Exports vN` folder, and never overwrite a delivered version.

## Workflow

### 1. Gather the brief

- **Notion ticket.** Fetch it with Notion `notion-fetch`. Extract:
  - the Editor Ticket instructions;
  - the creator-version Frame link and the raw footage link;
  - the hooks table and the script table (on-screen text per section);
  - the offer, T&Cs and variation count;
  - the persona, plus any names that appear (e.g. the dog's name).
- **Frame.io.** Call `mandatory_init`; Hambi's account is `eb4ebb8d-7328-4a67-b3ac-aa654a019fd1`.
  - The ticket link is usually a **version stack**. Use `list_version_stack_versions`, then read comments on the newest version **and** the older ones.
  - List the parent folder to find the sibling hook stacks (Hook 1/2/3) and read their comments too. "Same feedback throughout" means every hook gets the same fixes.
- **Footage.** Try the Google Drive connector first (`search_files` with `parentId = '<folder id>'`).
  - If the folder belongs to the creator's personal account, its subfolders usually list as empty. Don't burn calls: ask the user to download the folder into a connected local folder (e.g. `D:\Hambi\04. Post Production Lead\<CLIENT>_<CONCEPT>_raw`).
  - Then stage the files with `device_stage_files` and copy them from `/mnt/user-data/uploads/...` into a work dir.
  - Files called "Raw" from creators are often their finished cut with the text removed. That's usually the best plate to revise from. Check by comparing durations with the Edited files.

### 2. Analyse

- **Probe each file:** `ffprobe` for codec, fps, size and `color_transfer`. `arib-std-b67` means iPhone HLG HDR, which needs tone-mapping.
- **Contact sheets:** `fps=1,scale=160:-1,tile=10x3` per hook. Read them to understand shot order.
- **Cut points:** `scale=270:-1,select='gt(scene,0.2)',showinfo`. Gives scene cuts per hook.
- **Existing text timing:** crop the text band of the Edited files and add a `drawtext` timestamp:
  `fps=1,crop=1080:420:0:250,scale=300:-1,drawtext=text='%{pts\:hms}':...,tile=5x6`
- **Picking a frame to hold or reuse:** score sharpness with OpenCV (Laplacian variance over the product area) and look at the best tone-mapped still before committing.
- **Duplicates:** if a new opener reuses a body shot, find and remove the later repeat (standards rule B4).

### 3. Cut sheet and style frames (approval gate)

Write `<CLIENT>_<CONCEPT>_CutSheet_vN.md` to `/mnt/user-data/outputs/<CLIENT>_<CONCEPT>/`. It contains:

- **Global changes:** a table mapping each client note to its fix. Include what is deliberately kept and why.
- **Text cards:** the exact copy for each card. Check spelling and brand names against the standards (rules C1–C7).
- **Timings per hook:** in/out seconds, picture, and which card is on screen.
- **Open points:** partial fixes, missing T&Cs, font stand-ins, and anything the footage can't deliver.

Render **style frames**: 4–5 tone-mapped stills with the new cards overlaid, `hstack`ed into one JPG. Check the cards stay clear of the product and inside the safe zone. Then ask for "APPROVED vN" or tweaks, and keep the chat summary short.

### 4. Build `spec.json`

```json
{
  "client": "BD", "concept": "C5_DogFood_ChristmasFineDining", "version": 2,
  "fps": 30, "width": 1080, "height": 1920, "hdr_hlg": true,
  "device_root": "D:\\Hambi\\04. Post Production Lead\\BD_C5_raw",
  "sources": {"h1": {"local": "src/h1_raw.mov", "device": "Christmas\\Hook 1 Raw.mov", "frames": 739}},
  "card_style": {"font_bold": "fonts/DMSans-Bold.ttf", "font_regular": "fonts/DMSans-Medium.ttf",
                 "box": [0,58,58], "text": [255,255,255], "y_top": 330, "max_w": 860, "radius": 30},
  "cards": {"hook1": {"lines": [["My dog's Christmas dinner is better than mine this year", 56, true]]},
            "critic": {"lines": [["THE CRITIC'S REVIEW:", 52, true]], "stars": 5}},
  "hooks": {
    "H2": {
      "audio": "h2",
      "segments": [
        {"src": "h1", "in": 6.433, "out": 6.833, "speed": 0.4},
        {"src": "h2", "in": 1.0,   "out": 7.633},
        {"src": "h2", "in": 8.067, "out": 8.833, "fill": 1.2},
        {"src": "h2", "in": 8.833, "out": null}
      ],
      "overlays": [["hook2", 0, 3.97], ["chef", 3.97, 7.63], ["end", 21.5, null]],
      "notes": [["Opener", "Sealed-pack opener from H1 6.43-6.83 at 40%", 0]]
    }
  }
}
```

Rules for segments:

- `speed` is a fraction of real time; `fill` is the target duration in seconds. Use one or the other.
- **No freeze-frame holds.** They don't survive XML import. Get the length by slowing the clip down instead.
- Keep the hook's **original audio continuous**. Picture edits replace video only, so the total length should match the source audio.

### 5. Render

Fonts: DM Sans comes from jsDelivr (`@fontsource/dm-sans@5.0.18/files/dm-sans-latin-{500,700}-normal.woff2`). Convert to TTF with fontTools plus brotli. GitHub raw URLs are blocked in this environment.

**Cards** (Pillow): render each as a transparent 1080×1920 PNG.

- One rounded box in the brand colour, with a soft Gaussian shadow (blur 14, alpha 90).
- Lines word-wrapped to `max_w` and centred.
- Draw stars as polygons, because brand fonts often lack the ★ glyph.
- Keep cards inside safe zones (top edge at y ≥ 270 px, clear of the bottom 35%) and off the product.

**Video** (FFmpeg `filter_complex`):

- **Segments.** `[i:v]split=N` before multiple trims of the same input. Each piece gets `trim=start:end`, then `setpts=<1/speed>*(PTS-STARTPTS)`, then `fps=30`. Join with `concat=n=K:v=1:a=0`, then `tpad=stop_mode=clone:stop_duration=0.2` so the picture is never shorter than the audio.
- **HLG to SDR:**
  `zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p`
- **Cards.** Chain `overlay=0:0:enable='between(t,a,b)'` for each card.
- **Audio.** `loudnorm=I=-14:TP=-1:LRA=11,aresample=48000,volume=-1.5dB`. Single-pass loudnorm lands around −12.5 LUFS, so the trim corrects it to about −14. Verify with `ebur128`.
- **Encode.** `libx264 -crf 18 -preset medium -pix_fmt yuv420p`, bt709 colour tags, AAC 192k, `-shortest -movflags +faststart`.
- **Memory.** Render hooks **one at a time**. Running three in parallel with multiple trims gets the job SIGKILLed for running out of memory.

**QC each hook:**

- Duration within 0.1 s of the source.
- Integrated loudness −14 ±0.5 LUFS, true peak below −1 dBTP.
- A frame strip at every card change and every edit point. Look at it before delivering.
- The `editing-standards.md` checklist.

### 6. Deliver each round

Use `SendUserFile` with `display: render` for the MP4s, then `device_commit_files` with each **fileUuid** into `<device_root>\Exports vN\`. Committing script-made MP4s via `stagedPath` returns HTTP 400.

In the chat, say in 2–3 lines what changed and flag anything you'd change next. Then ask for notes with timestamps.

### 7. Feedback loops

For each round:

1. Map every note to a `spec.json` change.
2. Bump `version`.
3. Re-render only the hooks that changed (copy unchanged hooks forward under the new `vN` name).
4. QC, then deliver to `Exports vN`.

After each round, sort the feedback:

- **Applies to all clients:** offer to add it to `editing-standards.md`.
- **Applies to one client:** goes into Client overrides / Brand Hub.
- **Applies to this ad only:** stays on the ticket.

### 8. Final XML (only after sign-off)

Build **one** FCP7 xmeml v4 file: `<xmeml><project><children><bin><name>…Sequences</name><children>` followed by one `<sequence>` per hook.

**Files**

- Each source or card file is declared in full **once** (`<file id=…>` with `pathurl`, rate, duration and media); later uses are `<file id="…"/>`.
- `pathurl` format: `file://localhost/D%3a/<url-quoted path>`, pointing at the user's local footage and `<device_root>\Premiere\cards\*.png`.

**Tracks per sequence**

- **V1:** a clipitem per spec segment (`start`, `end`, `in`, `out` in frames). Speed changes go in a `timeremap` filter whose `speed` parameter is a percentage.
- **V2:** the card PNGs, with `<stillframe>TRUE</stillframe>` and duration 108000.
- **A1:** the hook's audio, with `sourcetrack trackindex 1`.

**Markers at frame 0** (plus any spec notes):

- **Grade:** HLG source; set SDR or apply the conversion LUT.
- **Audio:** the render was −14 LUFS; the clip is at 0 dB.
- **Cards:** these are flattened PNGs; rebuild as Essential Graphics if text needs editing.

**Validate:**

- the file parses (`xml.dom.minidom`);
- the sequence count equals the hook count;
- clipitem ids are unique;
- each file id is fully defined only once.

Send the XML and card PNGs with `SendUserFile` (`attach`), then commit them to `<device_root>\Premiere\` (cards in `cards\`).

Tell the user:

- Import with File → Import. It brings in one bin with all hooks.
- What doesn't carry over: grade, loudness, card editability, and any speed or hold approximations.
- Offer to test-import it through the Premiere MCP if Premiere is open.

## Naming

- MP4: `<CLIENT>_<CONCEPT>_H<n>_v<N>.mp4`
- Cut sheet: `<CLIENT>_<CONCEPT>_CutSheet_v<N>.md`
- XML: `<CLIENT>_<CONCEPT>_ALL_HOOKS_v<N>.xml`

## Known limits (say these up front when they apply)

- If the creator won't reshoot, a missing shot can only be faked from existing footage. Flag it as a partial fix.
- Burned-in creator text can only be removed if a text-free version exists. Otherwise the new cards have to cover it.
- Brand fonts aren't on the machine unless the user supplies them.
- No dialogue means no subtitles. If there is dialogue, transcribe with faster-whisper (`small.en`, int8) and check every caption against the audio (standards C1).