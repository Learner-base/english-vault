# Cheatsheet — scripts, skills, hooks

Short version of the day-to-day commands. Full layout: [architecture.md](architecture.md).

## The one command you must not forget

```
python3 dev/scripts/build_index.py
```

Regenerates **`dev/index.html`** (the file browser), **`dev/player.html`** (the road audio
playlist), **`dev/progress.html`** (what you're studying now),
**`generated/translate/translate.html`**, **`generated/dictation/dictation.html`**
and **`generated/paraphrase/paraphrase.html`**.
Run it after you add, rename, move or delete **any** file — or after carding new words.
Never hand-edit those six — they are generated.

Because the dictation is rebuilt here too, **every new word you card is in the spelling
drill straight away**; words you're still learning are never filtered out as "too easy".

`dev/progress.html` lists the in-progress decks, the review decks and the drill pages,
**newest first**, and puts a `now` badge on the newest item of each group — so the deck
you just built is always the one it points at. To hold one file at the top whatever
gets generated later, pin it:

```
python3 dev/scripts/build_progress.py --pin C20-r1-vocabs.html    # --unpin, --list
```

Pins live in `vocab/studying-now.md` and are dropped automatically when you retire
the deck. The drills group is never auto-highlighted — only pin it if you want it.

The browser lists only six top-level folders — `docs`, `generated`, `listening`,
`reading`, `vocab`, `writing` — and what is inside them. Loose files at the repo root,
`dev/templates/`, and every dotfile (`.gitkeep`, `.gitignore`, …) stay hidden. To make
another folder visible, add it to `TOP_LEVEL` in `dev/scripts/build_index.py`.

## Full screen button

Every listening and reading test has a **Full screen** button at the right-hand end of
its header, and so do `dev/templates/reading.html` / `listening.html`, so newly
generated tests get it for free. If a hand-made test ever lacks one:

```
python3 dev/scripts/add_fullscreen.py            # every test + both templates
python3 dev/scripts/add_fullscreen.py path.html  # just one
```

It is idempotent — files that already have the button are left untouched.

## Skills (say it in plain words, Claude picks the skill)

| Say this | Skill | What happens |
|---|---|---|
| "make a reading test from this PDF + answers" | `reading-generate` | interactive 3-passage reading HTML |
| "make a listening test from these audios + script" | `listening-generate` | 4-section listening HTML with audio |
| "build a vocab deck from this passage + these words" | `vocab-deck` | flashcard HTML + `learning.json` + `known.md` |
| "I finished this test" | `move-to-done` | `undone/` → `done/` + rebuild |
| "I finished this vocab deck" | `vocab-deck-done` | deck → `done/`, words → `need-to-review.json`, **review page**, rebuild **+ commit** |
| "make me a dictation" | `dictation` | spelling quiz from your vocab + `vocab/for-dictation.md` |
| "how do I remember this word?" | `keyword-mnemonics` | Uzbek sound-alike + absurd story |
| "add these hard sentences" | `translate-practice` | EN → Uzbek practice page |
| "save the synonyms this test used" | `paraphrase-bank` | question wording ↔ passage wording + practice page |
| "I'm studying this one now" | `studying-now` | pins it to the top of the progress page |
| "what should this file be called?" | `test-naming` | the short-name convention |

Each skill's own `SKILL.md` lives in `.claude/skills/<name>/`, and every generator ends
by rebuilding the index for you. Only `vocab-deck-done` commits (never pushes) —
everything else leaves the changes for you to review.

## Where things live

The repo root holds only what you study with — the five folders above. Everything else
lives in **`dev/`**: the three pages, the build scripts, the templates, the docs and
loose notes. Online nothing changes — `vercel.json` rewrites `domain.com/` and
`domain.com/progress.html` to the `dev/` copies. Offline, open `dev/index.html`.

```
reading/  listening/       undone/ … → done/ …      source tests
generated/reading|listening|vocab|dictation|translate   study HTML
generated/vocab/inprogress/ → generated/vocab/done/     vocab decks
generated/vocab/review/    review pages, auto-built from need-to-review.json
vocab/learning.json        cards you're still learning
vocab/need-to-review.json  cards from finished decks (drives the review pages)
vocab/known.md             every word you've ever carded (never pruned)
vocab/glossary.json        word help for the translate page (words with no card)
vocab/for-dictation.md     words that must appear in the dictation deck
vocab/studying-now.md      files pinned to the top of progress.html
vocab/translations.json    practice sentences + their chunk breakdowns
vocab/paraphrases.json     question wording <-> passage wording, per test

dev/scripts/    the generators (build_index, build_player, build_translate,
                build_progress, build_paraphrase)
                plus add_fullscreen.py (header full-screen button for the tests)
dev/templates/  the reading / listening / vocab page templates
dev/docs/       this file + architecture.md
```

## Hooks — automation you don't have to remember

Hooks live in `.claude/settings.json` and fire on their own. To add one, just tell
Claude *"add a hook that …"* — it edits the file for you.

**What you already have**

| Setting | Effect |
|---|---|
| `permissions.ask` on `git commit` / `git push` | Claude must ask you before either |
| `PostToolUse` → `.claude/hooks/structured-change-reminder.py` | when a build script or template is edited, reminds Claude to check the matching `SKILL.md` |

**Worth adding**

Auto-rebuild the index after every file change, so you can never forget it:

```json
"PostToolUse": [
  { "matcher": "Edit|Write",
    "hooks": [{ "type": "command",
      "command": "python3 \"$CLAUDE_PROJECT_DIR/dev/scripts/build_index.py\" >/dev/null" }] }
]
```

A "turn finished" sound, so you can look away while a long test generates:

```json
"Stop": [
  { "hooks": [{ "type": "command", "command": "afplay /System/Library/Sounds/Glass.aiff" }] }
]
```

**The events**: `PostToolUse` (after a tool runs) · `PreToolUse` (before — can block it) ·
`Stop` (Claude finished answering) · `UserPromptSubmit` (add context to every message).

## Habits that save the most time

1. Describe the goal, not the steps — "I finished C20-r1" beats explaining the move.
2. Batch: give a passage **and** its unknown words in one message; the deck, the JSON
   updates and the index rebuild all happen in one pass.
3. Never edit `dev/index.html` / `dev/player.html` / `translate.html` by hand — the next rebuild
   overwrites them.
4. Drop future ideas in `future-prompts.md`; it's your queue, not part of the site.
