---
name: reading-generate
description: Generate a Cambridge-style interactive IELTS Academic Reading test as a single self-contained HTML (3 passages, 40 questions, timer, submit-confirm modal, band-score results dashboard, in-passage answer-location highlights, bottom question navigator) from a user-provided source — passages + questions + an answer key. Built from dev/templates/reading.html so every generated test looks and behaves identically. Use when the user gives a reading test (PDF / text / images / existing HTML) plus its answers and wants a clean, ad-free interactive study version.
---

# Reading test generator

Turn a provided reading test (passages + questions) and its answer key into one
self-contained interactive HTML that is **byte-for-byte identical in look and behaviour**
to the Cambridge 20 reading tests: full-width two-pane layout, 60-minute timer,
Submit → confirm modal → check-once, animated band-score results dashboard with a
filterable per-question review, green answer-location highlights inside the passage
after submit, and a bottom passage/question navigator.

Everything visual/behavioural lives in `dev/templates/reading.html` (engine + CSS + body).
You only ever author **data**: three JS objects — `TEST`, `EXPL`, `answerHighlightQuotes`.
`scripts/build_reading.py` injects them, verifies the highlight quotes really occur in
the passages, checks the script parses, and writes the final file.

## Inputs (from the user)
- **The test content** — passages + all questions. May be a PDF, pasted text, images, or
  an existing HTML. The reading passages are the substance; reproduce them faithfully.
- **The answer key** — the correct answers for all 40 questions (often a separate file).
  Do not invent answers; if the key is missing, ask for it.
- **Naming** — book/test number for the title, header and badge. The **output filename**
  follows the [test-naming](../test-naming/SKILL.md) convention: `C{book}-r{test}.html`
  (e.g. Cambridge 20, Test 1 → `C20-r1.html`), kept under `reading/undone/cambridge/<book>/`.

## Where files go
- **Generated test → `reading/undone/cambridge/<book>/C{book}-r{test}.html`** (short name,
  see [test-naming](../test-naming/SKILL.md); or the path the user specifies). Undone until
  the user has done it; they move solved tests to `reading/done/…`.
- Scratch files (extracted text, `data.js`, quote lists) → the session scratchpad, never the repo.
- The base template stays at `dev/templates/reading.html`; never copy the copyrighted passage into it.

## Data schema — the three objects in `data.js`

### `const TEST = { passages:[…], groups:[…] }`
`passages` — one per part, in order:
```
{ part:1, range:"1–13",
  instructions:"You should spend about 20 minutes on Questions 1–13, which are based on Reading Passage 1 below.",
  title:"…", subtitle:"…"|"",          // subtitle is the italic line under the title
  body:[ "para 1", "para 2", … ] }      // each string = one <p>; HTML allowed
```
For A–G / A–F passages, start each paragraph string with `"<strong>A</strong>&nbsp;&nbsp;…"`.
Put footnotes as a final `"<em class='text-sm text-gray-500'>*note…</em>"` paragraph.

`groups` — question blocks in order. Every group has `part`, `heading` ("Questions 7–13"),
and `rubric` (HTML). Pick the `type`:

- **`choice`** — pick one label from `options`. Used for TRUE/FALSE/NOT GIVEN,
  YES/NO/NOT GIVEN, and all letter-matching (paragraph / heading / people / sentence-endings).
  For letter grids add `inline:true`. Each question: `{id, prompt, answer:"B"}`.
  ```
  { part:1, heading:"Questions 1–6", rubric:"…TRUE / FALSE / NOT GIVEN…",
    type:"choice", options:["TRUE","FALSE","NOT GIVEN"],
    questions:[ {id:1, prompt:"…", answer:"FALSE"}, … ] }
  ```
  Heading matching → `options:["i","ii",…], inline:true`; put the List of Headings in `rubric`.
  People/sentence-ending matching → `options:["A","B","C"…], inline:true`; put the list in `rubric`.
- **`mc`** — single multiple-choice with option text. `{id, prompt, answer:"C",
  options:[["A","…"],["B","…"],["C","…"],["D","…"]]}`.
- **`template`** — note / summary / sentence completion. `template` is HTML with `[[id]]`
  placeholders; each becomes a numbered blank. Questions: `{id, answer:["word","altspelling"]}`
  (array = accepted variants; answers are case/whitespace-insensitive).
  For a **letter-summary with a dropdown** (list of phrases A–H), add
  `selectOptions:[["A","A  phrase"],…]` to the group and give each question a letter answer:
  `{id:33, answer:"F"}`.
- **`multi`** — "choose TWO" (or N). One block spanning two ids; 1 mark per correct letter:
  ```
  { part:2, type:"multi", key:"m23", ids:[23,24], pick:2, heading:"Questions 23 and 24",
    rubric:"Choose <strong>TWO</strong> letters, A–E.", prompt:"Which TWO …?",
    options:[["A","…"],…["E","…"]], answer:["A","C"] }
  ```

### `const EXPL = { "1":"one-line why…", … }`
Per-question explanation shown in the results answer-review. Quote the exact supporting
words from the passage. Cover every question you can (aim for all 40).

### `const answerHighlightQuotes = { "1":"exact passage substring", … }`
For each question, an **exact substring of the passage** (whitespace-flexible, case-insensitive)
to highlight green with a `Q#` tag after submit.
- **Skip NOT GIVEN / NG** questions (there is no location) — just omit that id.
- For matching/heading questions, use a short representative phrase from the correct paragraph.
- Avoid straight/curly apostrophe mismatches: prefer phrases without apostrophes.
- `build_reading.py` **fails** if any quote is not found, so fix/trim until all match.

## Rules
1. **Exactly 40 questions**, ids 1–40, split Part 1 = 1–13, Part 2 = 14–26, Part 3 = 27–40
   (the engine's part ranges are fixed). `multi` groups occupy their listed ids.
2. **Answers come from the user's key** — never guess. Map each key entry to its id; verify
   the count is 40.
3. **Reproduce passages/questions faithfully** from the source the user gave you.
4. **No ads / branding / external trackers** — the template is already clean; keep it that way.

## Steps
1. **Extract** the source. For PDFs use PyMuPDF (`fitz`) to dump text to scratch; for images
   render pages and read them. Confirm you have all passages, all 40 questions, and the key.
2. **Author `data.js`** in scratch: the three objects above (double-quoted strings so
   apostrophes are safe). Order groups by question number.
3. **Build**:
   ```
   python .claude/skills/reading-generate/scripts/build_reading.py \
     --data <scratch>/data.js \
     --title  "Cambridge 20 — Reading Test 1" \
     --header "Cambridge IELTS 20 — Reading Test 1" \
     --badge  C20 \
     --out    "reading/undone/cambridge/cambridge-20/C20-r1.html"
   ```
   It verifies quotes, checks syntax, and writes the file. Fix any reported quote misses
   (trim to an exact substring) or id-count warnings, then re-run.
4. **Refresh the main page** so the new test appears in the root file browser:
   ```
   python3 dev/scripts/build_index.py
   ```
5. **Verify** (no browser needed): the script parses (the build already `node --check`ed it);
   optionally spot-check that `ids` = 1..40 and the answer key lines up.
6. **Commit** — only with the user's go-ahead (they review first). Commit one test per commit;
   do not push unless asked.

## Notes
- If the template's markup changes, `build_reading.py` fails loudly on the missing marker or
  header string — update the template or the script's patch targets together.
- `dev/templates/reading.html` ships with a short ORIGINAL placeholder sample that demonstrates
  every group type; open it directly to see the schema working. Never overwrite that sample
  with copyrighted passage text.
