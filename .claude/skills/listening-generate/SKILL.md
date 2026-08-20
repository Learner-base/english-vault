---
name: listening-generate
description: Generate a Cambridge-style interactive IELTS Listening test as a single self-contained HTML (4 sections, 40 questions, embedded auto-chaining audio, submit-confirm modal, band-score results dashboard, and a full transcript shown on the right after submit with in-place answer-location highlights) from a user-provided source — the questions, an answer key, the section audio files, and the audioscript. Built from templates/listening.html so every generated test looks and behaves identically to the Cambridge 20 listening tests. Use when the user gives a listening test (PDF / text / images) plus its audio and answers and wants a clean, ad-free interactive study version.
---

# Listening test generator

Turn a provided listening test (4 parts, 40 questions), its answer key, its four section
audio files, and its audioscript into one self-contained interactive HTML that is identical
in look and behaviour to the Cambridge 20 listening tests: questions on the left, an audio
player + transcript pane on the right, a 40-minute timer, Submit → confirm modal → check-once,
an animated band-score results dashboard with a filterable per-question review, and — after
submit — the full transcript with green answer-location highlights (`Q#` tags).

Everything visual/behavioural lives in `templates/listening.html` (engine + CSS + body).
You only ever author **data**: the JS objects `TEST` (with `sections`, `groups`, `transcript`),
`EXPL`, `answerHighlightQuotes`, and an `AUDIO` array of placeholders.
`scripts/build_listening.py` splices them in, embeds the four audio tracks as base64, verifies
the highlight quotes really occur in the transcript, checks the script parses, and writes the file.

## Inputs (from the user)
- **The questions** — all 40, in 4 parts. May be a PDF, pasted text, or images.
- **The answer key** — the correct answers for all 40 questions. Do not invent answers.
- **The audio** — the four section files (Part 1–4), e.g. `T1S1.m4a … T1S4.m4a`. They are
  embedded and play continuously, auto-advancing Part 1→2→3→4.
- **The audioscript** — the transcript. Needed for the right-hand transcript pane and the
  answer highlights. If part of it is missing, still build it: just omit highlights for the
  answers that aren't in the text (they are still scored and shown in the results).

## Where files go
- **Generated test → `listening/undone/cambridge/<book>/C{book}-l{test}.html`** (short name,
  see [test-naming](../test-naming/SKILL.md); undone until done).
- Scratch files (extracted text, `data.js`, rendered map images) → the session scratchpad, never the repo.
- The base template stays at `templates/listening.html`; never copy a copyrighted transcript into it.

## Fixed part ranges
Part 1 = Q1–10, Part 2 = Q11–20, Part 3 = Q21–30, Part 4 = Q31–40 (the engine is fixed).
`multi` groups occupy their listed ids.

## Data schema — the objects in `data.js`

### `const AUDIO = ["__AUDIO_0__","__AUDIO_1__","__AUDIO_2__","__AUDIO_3__"];`
One placeholder per section, in Part 1–4 order. The build script copies the four audio files into
the shared `/audio/cambridge-<badge>/` folder and replaces the placeholders with their paths
(e.g. `/audio/cambridge-20/test-1-part-1.m4a`) — so the tests and `/player.html` share one copy.

### `const TEST = { sections:[…], groups:[…], transcript:{…} }`
`sections` — one per part: `{ part:1, head:"short label", instructions:"Questions 1–10 · …" }`.

`groups` — question blocks in order; each has `part`, `heading`, `rubric` (HTML). Pick `type`:
- **`template`** — form / note completion. `template` is HTML with `[[id]]` blanks. Questions:
  `{id, answer:["word","altspelling"]}` (array = accepted variants; case/space-insensitive).
- **`mc`** — single multiple choice: `{id, prompt, answer:"B", options:[["A","…"],["B","…"],["C","…"]]}`.
- **`choice`** with `inline:true` — letter-matching / map-labelling / matching-from-a-box. Put the
  box list (or `<img src='__MAPIMG__'>` for a map) in `rubric`; `options:["A","B",…]`; each question
  `{id, prompt, answer:"C"}`.
- **`multi`** — "choose TWO". One block over two ids; 1 mark per correct letter:
  `{part, type:"multi", key:"m12", ids:[12,13], pick:2, heading, rubric, prompt, options:[["A","…"],…], answer:["A","C"]}`.

`transcript` — `{ 1:[turns], 2:[…], 3:[…], 4:[…] }`. Each turn is `{who:"WOMAN", text:"…"}` or a
system note `{sys:"Before you hear the rest…"}`. Reproduce the audioscript faithfully; strip any
website ads/nav lines (e.g. "Advertisements", "SubscribingTo …").

### `const EXPL = { "1":"one-line why…", … }`
Per-question explanation shown in the results answer-review. Quote the exact spoken words.

### `const answerHighlightQuotes = { "1":"exact transcript substring", … }`
For each question, an **exact substring of that part's transcript** (whitespace-flexible,
case-insensitive) to highlight green with a `Q#` tag after submit.
- **Omit** ids whose answer isn't clearly spoken in the available transcript.
- Prefer phrases **without apostrophes** (curly vs straight quotes cause mismatches).
- `build_listening.py` **fails** if any quote is not found, so trim until all match.

## Steps
1. **Extract** the source (PyMuPDF `fitz` for PDFs; render pages for images/maps). Confirm you
   have all 40 questions, the key, the four audio files, and the audioscript.
2. **Author `data.js`** in scratch: `AUDIO` + the three objects, double-quoted strings. Map each
   answer-key entry to its id and verify the count is 40.
3. For any **map/diagram**, render the PDF page region to a PNG (cropped free of branding) and put
   `<img src='__MAPIMG__' …>` in that group's rubric; pass the PNG with `--map`.
4. **Build**:
   ```
   python .claude/skills/listening-generate/scripts/build_listening.py \
     --data <scratch>/data.js \
     --audio "T1S1.m4a,T1S2.m4a,T1S3.m4a,T1S4.m4a" \
     --title  "Cambridge 20 — Listening Test 1" \
     --header "Cambridge IELTS 20 — Listening Test 1" \
     --badge  20 \
     --out    "listening/undone/cambridge/cambridge-20/C20-l1.html" \
     [--map <scratch>/part2_map.png]
   ```
   It verifies quotes, embeds audio, checks syntax, and writes the file. Fix any reported quote
   misses (trim to an exact substring) or id-count warnings, then re-run.
5. **Refresh the main page** so the new test appears in the root file browser:
   ```
   python3 scripts/build_index.py
   ```
6. **Verify** (no browser needed): the build already `node --check`ed the script; optionally
   simulate scoring in Node (perfect answers should give 40/40) and confirm ids = 1..40.
7. **Commit** — only with the user's go-ahead. Commit one test per commit; do not push unless asked.

## Notes
- Audio is stored once in `/audio/cambridge-<badge>/` and referenced by path (root-absolute
  `/audio/…`), so each test HTML stays small (~90 KB) and `/player.html` reuses the same files.
  The site is served from the repo root (Vercel), where `/audio/…` resolves correctly.
- After building, `/player.html` picks up the new tracks automatically on the next
  `python3 scripts/build_index.py` (see the `player-update` skill).
- If the template's markup changes, `build_listening.py` fails loudly on a missing marker or
  placeholder — update the template or the script's patch targets together.
- `templates/listening.html` ships with a short ORIGINAL placeholder sample (empty AUDIO) that
  demonstrates every group type; open it directly to see the schema working. Never overwrite that
  sample with copyrighted transcript text.
- The engine also accepts embedded `data:` audio URIs in the AUDIO array (older self-contained
  form); the current builder uses `/audio/…` paths instead. Both play in the same player.
