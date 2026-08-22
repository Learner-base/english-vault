---
name: vocab-deck-done
description: Retire a finished vocab deck — move its HTML from generated/vocab/inprogress/ to generated/vocab/done/, move that set's cards out of vocab/learning.json into vocab/need-to-review.json, and rebuild index.html. Use when the user says they've finished/learned a vocab deck, or asks to mark a vocab set done / move its words to review.
---

# Retire a finished vocab deck

When the user has finished studying a vocab deck, file it under `done/` and move its
words to the review pile so they stop showing up as "still learning".

## What it does

`scripts/vocab_done.py` takes one or more decks (an HTML path, or just the set name)
and, for each:

1. Works out the **set name** — the filename without `-vocabs.html`
   (`cambridge-18-test-1-reading-1-vocabs.html` → `cambridge-18-test-1-reading-1`).
   That is also the key used inside `learning.json`.
2. `git mv`s the deck HTML `generated/vocab/inprogress/` → `generated/vocab/done/`
   (creates `done/` if missing; plain move if the file isn't tracked).
3. Moves that key's cards from `vocab/learning.json` into `vocab/need-to-review.json`,
   merging (and de-duplicating by `w`) if the key is already there.
4. Rebuilds `index.html` via `scripts/build_index.py`.

Each step is skipped harmlessly if it's already been done, so re-running is safe.

## Usage

```
python3 .claude/skills/vocab-deck-done/scripts/vocab_done.py cambridge-18-test-1-reading-1
python3 .claude/skills/vocab-deck-done/scripts/vocab_done.py generated/vocab/inprogress/C20-r1-vocabs.html
```

Pass several decks at once. `--no-index` skips the rebuild (use it only if you're
batching and will rebuild yourself).

## Notes

- `vocab/need-to-review.json` has the same shape as `learning.json`: `{set name: [cards]}`.
- Words stay in `vocab/known.md` — that list is the full history and is never pruned here.
- The [dictation](../dictation/SKILL.md) deck builds from `known.md` + `learning.json`,
  so retired words keep their spelling practice via `known.md` but lose their rich
  meaning/example lines. That's intended.
- `index.html` and `player.html` are generated — never hand-edit them.
- **Commit only with the user's go-ahead**; the script never commits.
