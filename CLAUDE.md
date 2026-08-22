# english-vault

An IELTS/English self-study vault of standalone HTML tools. See `dev/docs/architecture.md`
for the full layout and the source → generate → study idea.

## Always keep the main page in sync
`index.html` (repo root) is the site's main page: a file browser of the whole project.
It is **generated** from the current file tree by `dev/scripts/build_index.py`.

**Whenever you create, rename, move, or delete any file or folder** (a generated study
HTML, a new source test, a data file — anything except `.claude/`, `.git/`), run:

```
python3 dev/scripts/build_index.py
```

as the final step, so the main page shows the new content. Skills that generate files
must do this too (it is listed in their SKILL.md).

## Repo layout
The root holds only the study content — `generated/`, `listening/`, `reading/`,
`vocab/`, `writing/` and the three pages `index.html`, `progress.html`, `player.html`
— so it stays free of distractions. Everything else lives in **`dev/`**:
`dev/scripts/` (generators), `dev/templates/` (page templates), `dev/docs/`, and loose
notes. Site URLs are unchanged: `index.html` is still served at the domain root.
