---
name: studying-now
description: Pin (or unpin) a file so it stays at the top of progress.html with a "pinned" badge — the "this is what I'm on right now" list, kept in vocab/studying-now.md. Use when the user says they're now studying / working on a particular deck or page, asks to feature or highlight a file on the progress page, or asks what they're currently studying.
---

# What I'm studying now

`dev/progress.html` lists everything in progress, newest first, and badges the
newest item of each group. That is a good default, but it means the badge moves
to whatever was generated last — which is not always what you're actually on.

**Pinning overrides that.** A pinned file is held at the top of its group with a
`pinned` badge, however many newer files appear afterwards.

## The list

`vocab/studying-now.md` — one file name per line, under whatever header prose the
file has:

```
- C20-r1-vocabs.html
```

The bare name is enough; a repo path works too (only the file name is stored).
Order matters: the first pinned file in a group is listed first.

## Pin / unpin

```
python3 dev/scripts/build_progress.py --pin   C20-r1-vocabs.html
python3 dev/scripts/build_progress.py --unpin C20-r1-vocabs.html
python3 dev/scripts/build_progress.py --list
```

Each of those rewrites the list **and** regenerates `dev/progress.html`, so the
page is correct the moment the command finishes. Pass several names at once.
Editing `vocab/studying-now.md` by hand works just as well — the next rebuild
picks it up.

## Staying up to date by itself

- `python3 dev/scripts/build_index.py` regenerates the progress page, so it
  refreshes on every rebuild along with everything else.
- Retiring a deck with [vocab-deck-done](../vocab-deck-done/SKILL.md)
  **unpins it automatically** — a deck you've finished should not still be
  advertised as the thing you're studying.
- A pinned file that no longer exists is simply not shown; the line stays in the
  list, harmless, until you remove it.

## Which groups get an automatic badge

| Group | Highlighted when nothing is pinned |
|---|---|
| Still learning (`generated/vocab/inprogress`) | yes — the newest deck |
| To review (`generated/vocab/review`) | yes — the newest review deck |
| Drills (dictation, translation) | **no** — they're always-available tools, not
  something you work through, so they're only highlighted if you pin one |

Pinning anything in a group replaces that group's automatic badge, so there is
never both a `pinned` and a `now` highlight competing in the same list.

## Notes

- Pinning only reorders and badges. It never hides anything: unpinned files still
  appear underneath, newest first.
- Every row keeps its number, highlighted or not — the numbers are drawn with a CSS
  counter rather than the list marker, which a padded highlight box would swallow.
- The footer counts them: `8 items in progress · 2 highlighted`.
- `dev/progress.html` is generated — never hand-edit it.
