# Architecture for english-vault

This vault helps Muxsinjon learn English easily with new technologies. Instead of one
deployed website, it uses standalone **HTML files** — they are easy to generate, need no
deployment or testing, and open straight in a browser. The goal is learning English, not
building a perfect platform.

## Core idea: source → generate → study
1. **Source material** (reading / listening / writing tasks) lives in its topic folder.
2. A **template** in `templates/` defines the look and behaviour of a study tool.
3. A **skill** turns source material into a finished, self-contained study HTML.
4. Every generated HTML is written under **`generated/`** (never committed by hand — it is
   an output). Learning **data** (progress, word lists) lives in `vocab/`.

> A watcher relocates stray generated `.html` files into `generated/`. Always write
> generated output directly to `generated/…` so nothing gets moved or duplicated.

## Folders
- **generated/** — all generated, ready-to-use study HTML. Mirrors the source type.
    - `generated/vocab/` — vocabulary flashcard decks, one HTML per reading test
      (e.g. `cambridge-21-reading-3-vocabs.html`).
- **templates/** — reusable HTML templates that skills fill with data.
    - `vocab.html` — the flashcard study app (Flip / Recall / Cloze modes + a Structures
      section). Generic on its own; the build step patches in the front "form" line and the
      "related expressions" block per deck.
- **vocab/** — vocabulary **data** only (no generated HTML).
    - `known.md` — every word already seen in processed passages + questions, grouped by
      set (`## <set-name>`). Prevents re-flagging known words in future decks.
    - `learning.json` — all learning vocabulary cards, keyed by set name
      (`{ "cambridge-21-reading-3": [ …cards… ] }`).
- **reading/** — reading tests, as the exported test HTML (passages + questions embedded as
  a `const testData = {…}` object inside a `<script>`).
    - `reading/undone/…` — not yet studied. `reading/done/…` — completed.
    - organised by source/level, e.g. `reading/done/cambridge/cambridge-21/`.
- **listening/**, **writing/** — source material for those skills (same source → generate →
  study idea; generated output belongs under `generated/`).
- **docs/** — documentation. `architecture.md` — this file.
- **.claude/skills/** — project skills (see below).

## Skills
- **vocab-deck** (`.claude/skills/vocab-deck/`) — builds a vocabulary flashcard deck from a
  reading-test HTML plus a user-pasted list of unknown words.
    - `scripts/extract.py` — pulls the passages + questions out of the reading HTML
      (`testData` JSON) into readable text (the source of exact example sentences) and a
      unique word list for `known.md`.
    - `scripts/build.py` — injects the authored deck into `templates/vocab.html`, writes the
      HTML to `generated/vocab/`, keys the cards into `vocab/learning.json`, and adds the
      passage/question words to `vocab/known.md`. Runs are idempotent.
    - `SKILL.md` — the card schema, conventions, ordering rules, and step-by-step.
    - **Rules baked in:** the user always pastes the unknown-word list; all other
      passage/question words go to `known.md`; base words only (inflected form shown under
      the word); related collocations included in each card; question words first, then
      passage words; `learning.json` and `known.md` updated every run.
