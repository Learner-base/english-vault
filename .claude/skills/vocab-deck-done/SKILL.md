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
4. **Regenerates the review deck** `generated/vocab/review/<set>-review.html`
   (`scripts/build_review.py`) — see below.
5. Rebuilds `index.html` via `dev/scripts/build_index.py`.
6. **Commits** the result — staging only the paths it touches
   (`generated/vocab/`, the two vocab JSONs, `index.html`, `player.html`,
   `generated/translate/`), so unrelated work in progress stays uncommitted.
   It never pushes.

Each step is skipped harmlessly if it's already been done, so re-running is safe.

## Usage

```
python3 .claude/skills/vocab-deck-done/scripts/vocab_done.py cambridge-18-test-1-reading-1
python3 .claude/skills/vocab-deck-done/scripts/vocab_done.py generated/vocab/inprogress/C20-r1-vocabs.html
```

Pass several decks at once.

- `--no-commit` — leave everything in the working tree instead of committing.
- `--no-index` — skip the rebuild (only when batching and rebuilding yourself).

## The review deck

`scripts/build_review.py` builds one page per set in `generated/vocab/review/` from
`vocab/need-to-review.json`. It is the normal vocab deck (built from
`dev/templates/vocab.html`, same flip / recall / cloze modes) with **two hints** on the
card front:

1. **Show hint** — the collocation the word appeared in ("a striking new hall").
2. **Show example** — the full example sentence with the word blanked out (`———`),
   so it points at the word without giving it away.

The blanking handles multi-word entries ("as much as" is blanked as one phrase) and
inflections (`dangle` blanks `dangling`, `cavity` blanks `cavities`).

Run it on its own to rebuild every review page, or name sets to rebuild:

```
python3 .claude/skills/vocab-deck-done/scripts/build_review.py            # all
python3 .claude/skills/vocab-deck-done/scripts/build_review.py C20-r1     # one set
```

It also deletes review pages whose set is no longer in `need-to-review.json`.

## Notes

- `vocab/need-to-review.json` has the same shape as `learning.json`: `{set name: [cards]}`.
- Words stay in `vocab/known.md` — that list is the full history and is never pruned here.
- The [dictation](../dictation/SKILL.md) deck builds from `known.md` + `learning.json`,
  so retired words keep their spelling practice via `known.md` but lose their rich
  meaning/example lines. That's intended.
- `index.html` and `player.html` are generated — never hand-edit them.
- **Committing is pre-approved for this skill only** — the user explicitly asked it to
  commit, so you don't need to ask again when running it. Everywhere else the standing
  rule still holds: never commit without the user's go-ahead. The script never pushes.
