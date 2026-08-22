# Cheatsheet — scripts, skills, hooks

Short version of the day-to-day commands. Full layout: [architecture.md](architecture.md).

## The one command you must not forget

```
python3 scripts/build_index.py
```

Regenerates **`index.html`** (the file browser), **`player.html`** (the road audio
playlist) and **`generated/translate/translate.html`**. Run it after you add, rename,
move or delete **any** file. Never hand-edit those three — they are generated.

## Skills (say it in plain words, Claude picks the skill)

| Say this | Skill | What happens |
|---|---|---|
| "make a reading test from this PDF + answers" | `reading-generate` | interactive 3-passage reading HTML |
| "make a listening test from these audios + script" | `listening-generate` | 4-section listening HTML with audio |
| "build a vocab deck from this passage + these words" | `vocab-deck` | flashcard HTML + `learning.json` + `known.md` |
| "I finished this test" | `move-to-done` | `undone/` → `done/` + rebuild |
| "I finished this vocab deck" | `vocab-deck-done` | deck → `done/`, words → `need-to-review.json`, rebuild **+ commit** |
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
vocab/learning.json        cards you're still learning
vocab/need-to-review.json  cards from finished decks
vocab/known.md             every word you've ever carded (never pruned)
```

## Hooks that save time

Hooks live in `.claude/settings.json` and run **automatically** — no need to remember
them. The useful one here rebuilds the index whenever a file changes:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          { "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR/scripts/build_index.py\" >/dev/null" }
        ]
      }
    ]
  }
}
```

Other handy events: `Stop` (run something when Claude finishes a turn — e.g. a
`say done` notification), `UserPromptSubmit` (inject context into every prompt),
`PreToolUse` (block a tool before it runs). Ask Claude to "add a hook that …" and it
will edit `settings.json` for you.
