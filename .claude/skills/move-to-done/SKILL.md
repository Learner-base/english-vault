---
name: move-to-done
description: Move a finished test HTML from its undone/ folder to the matching done/ folder (creating the done folder if missing), then refresh index.html + player.html and flag any other references. Use when the user says they've finished/solved a test and it should move to done, or asks to mark a test done / move it out of undone.
---

# Move a test from undone → done

When the user has finished a test and wants it filed under `done/`, move it there and
keep every reference in sync.

## What it does

`scripts/move_done.py` takes one or more `.../undone/...` paths and, for each:

1. Computes the destination by swapping the `undone/` segment for `done/` — the rest of
   the path (provider, book folder, filename) is unchanged, e.g.
   `reading/undone/cambridge/cambridge-20/C20-r1.html`
   → `reading/done/cambridge/cambridge-20/C20-r1.html`.
2. **Creates the `done/` folder** (and any missing parents) if it doesn't exist yet.
3. Moves the file with `git mv` (preserves history; falls back to a plain move if the
   file isn't tracked).
4. Rebuilds the main page with `dev/scripts/build_index.py` — which also regenerates
   `dev/player.html` — so the file browser links and the road player point at the new path.
5. Greps the repo for any **other** place that still names the old path/filename
   (docs, `dev/progress.html`, cross-links…) and prints them to fix by hand.

## Usage

```
python3 .claude/skills/move-to-done/scripts/move_done.py "reading/undone/cambridge/cambridge-20/C20-r1.html"
```

Pass several paths at once to move a batch. The script prints each move, the rebuild
result, and a list of leftover references (or "none").

## After running

- If it listed other references, update those files, then re-run `build_index.py` if you
  changed anything the index depends on.
- **Grow the translation page**: a finished passage/test is the moment to add its difficult
  sentences (+ Uzbek) to `vocab/translations.json` — see
  [translate-practice](../translate-practice/SKILL.md).
- **Commit** only with the user's go-ahead (the script never commits). One logical move
  per commit is fine; do not push unless asked. See [never-commit-without-approval] in
  the user's memory.

## Notes

- `dev/index.html` and `dev/player.html` are generated — never hand-edit them; the rebuild owns
  their contents.
- The filename itself does not change on a move; naming is governed by
  [test-naming](../test-naming/SKILL.md).
- Moving a listening test within `listening/` keeps it in the player automatically (the
  player scans all of `listening/`, done or undone).
