# Cheatsheet — scripts, skills, hooks

Short version of the day-to-day commands. Full layout: [architecture.md](architecture.md).

## The one command you must not forget

```
python3 scripts/build_index.py
```

Regenerates **`index.html`** (the file browser), **`player.html`** (the road audio
playlist) and **`generated/translate/translate.html`**. Run it after you add, rename,
move or delete **any** file. Never hand-edit those three — they are generated.

The browser lists only six top-level folders — `docs`, `generated`, `listening`,
`reading`, `vocab`, `writing` — and what is inside them. Loose files at the repo root,
`templates/`, and every dotfile (`.gitkeep`, `.gitignore`, …) stay hidden. To make
another folder visible, add it to `TOP_LEVEL` in `scripts/build_index.py`.

## Skills (say it in plain words, Claude picks the skill)

| Say this | Skill | What happens |
|---|---|---|
| "make a reading test from this PDF + answers" | `reading-generate` | interactive 3-passage reading HTML |
| "make a listening test from these audios + script" | `listening-generate` | 4-section listening HTML with audio |
| "build a vocab deck from this passage + these words" | `vocab-deck` | flashcard HTML + `learning.json` + `known.md` |
| "I finished this test" | `move-to-done` | `undone/` → `done/` + rebuild |
| "I finished this vocab deck" | `vocab-deck-done` | deck → `done/`, words → `need-to-review.json`, **review page**, rebuild **+ commit** |
| "make me a dictation" | `dictation` | spelling quiz from your vocab |
| "how do I remember this word?" | `keyword-mnemonics` | Uzbek sound-alike + absurd story |
| "add these hard sentences" | `translate-practice` | EN → Uzbek practice page |
| "what should this file be called?" | `test-naming` | the short-name convention |

Each skill's own `SKILL.md` lives in `.claude/skills/<name>/`, and every generator ends
by rebuilding the index for you. Only `vocab-deck-done` commits (never pushes) —
everything else leaves the changes for you to review.

## Where things live

```
reading/  listening/       undone/ … → done/ …      source tests
generated/reading|listening|vocab|dictation|translate   study HTML
generated/vocab/inprogress/ → generated/vocab/done/     vocab decks
generated/vocab/review/    review pages, auto-built from need-to-review.json
vocab/learning.json        cards you're still learning
vocab/need-to-review.json  cards from finished decks (drives the review pages)
vocab/known.md             every word you've ever carded (never pruned)
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
      "command": "python3 \"$CLAUDE_PROJECT_DIR/scripts/build_index.py\" >/dev/null" }] }
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
3. Never edit `index.html` / `player.html` / `translate.html` by hand — the next rebuild
   overwrites them.
4. Drop future ideas in `future-prompts.md`; it's your queue, not part of the site.
