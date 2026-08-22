# english-vault

An IELTS/English self-study vault of standalone HTML tools. See `dev/docs/architecture.md`
for the full layout and the source → generate → study idea.

## Always keep the main page in sync
`dev/index.html` is the site's main page: a file browser of the whole project.
It is **generated** from the current file tree by `dev/scripts/build_index.py`.

**Whenever you create, rename, move, or delete any file or folder** (a generated study
HTML, a new source test, a data file — anything except `.claude/`, `.git/`), run:

```
python3 dev/scripts/build_index.py
```

as the final step, so the main page shows the new content. Skills that generate files
must do this too (it is listed in their SKILL.md).

That one command also regenerates `dev/player.html`, `dev/progress.html`,
`generated/translate/translate.html` and `generated/dictation/dictation.html` —
**all five pages are generated, never hand-edit them.** Rebuilding the dictation
there is what keeps newly carded words in the spelling drill automatically. `dev/progress.html` lists what you're studying newest-first and
highlights the newest deck in each group, so it follows the newest vocab deck by
itself; anything listed in `vocab/studying-now.md` is pinned above that.

## Repo layout
The root holds only the study content — `generated/`, `listening/`, `reading/`,
`vocab/`, `writing/` — so it stays free of distractions. Everything else lives in
**`dev/`**: the three pages (`index.html`, `progress.html`, `player.html`),
`dev/scripts/` (generators), `dev/templates/`, `dev/docs/` and loose notes.
`vercel.json` and `CLAUDE.md` must stay at the root (Vercel and Claude Code read them
there).

Site URLs are unchanged — `vercel.json` rewrites `/`, `/index.html`, `/player.html`
and `/progress.html` to their `dev/` copies. Locally, open `dev/index.html`.
