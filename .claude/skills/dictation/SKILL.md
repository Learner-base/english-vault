---
name: dictation
description: Generate a self-contained spelling-dictation quiz HTML into generated/dictation/ from the project's vocab (vocab/known.md + vocab/learning.json). The page speaks an English word aloud (browser text-to-speech); the user types what they hear; it checks spelling and, on a mistake, reveals the correct spelling and makes them retype it. Use when the user wants a listening/spelling test, a dictation drill, or to practise spelling words they collected.
---

# Spelling-dictation quiz builder

Build an interactive **spelling test**: the browser reads an English word aloud, the
user types it, the page checks the spelling. On a wrong answer it shows a letter-level
diff, logs the mistake, and forces the user to **retype the correct spelling** before
advancing. Everything is embedded into one HTML file, so it works opened directly
(`file://`) — no server, no build step at view time.

## When to use
The user wants to practise **spelling / listening**, asks for a "dictation", "spelling
test", or "read it and I type it" drill over the vocabulary they've collected.

## Inputs (already in the repo — no user paste needed)
- `vocab/known.md` — flat word list (the big pool).
- `vocab/learning.json` — rich cards; their base word `w` plus `def`/`uz`/`ex` become a
  meaning **hint shown after** the user answers (only for learning-set words).

The script reads both, dedupes, drops multi-word phrases (hard to dictate letter-perfect),
sorts, and embeds the result.

## How to build
```
python .claude/skills/dictation/scripts/build.py --repo-root . \
    --out generated/dictation/dictation.html
```
Re-run it any time the vocab files change — the word pool is regenerated and re-embedded.
Output goes to `generated/dictation/` (all generated artifacts live under `generated/`,
never in `vocab/`).

**Then refresh the main page** so the new/updated file shows in the root `index.html`
file browser:
```
python3 scripts/build_index.py
```

## What the page does (features)
- **Text-to-speech** via the Web Speech API (`en-GB` voice, "Speak slowly" toggle at 0.6×).
- **Sources**: All words / Learning-only / My mistakes (words previously misspelled).
- **Session length**: 15 / 30 / 50 / All, optional shuffle.
- **On correct**: green ✓, mark word mastered, show meaning hint (learning words only).
- **On wrong**: red, letter diff (struck-through wrong letters + underlined correct ones),
  log to the mistake list, and require an exact **retype** to continue.
- **Keyboard**: `Space` or `R` replays the audio, `Enter` checks the answer.
- **Progress** persists in `localStorage` (`dict_mastered_v1`, `dict_mistakes_v1`); a
  "reset progress" link clears it. The "My mistakes" source lets the user drill only the
  words they keep getting wrong.

## Notes / constraints
- No network; TTS is client-side. If a browser has no English voice, audio is silent but
  everything else still works.
- The page is self-contained — do NOT split CSS/JS out or add external assets.
- Keep the file at `generated/dictation/dictation.html` unless the user asks otherwise.
- Related: the [[vocab-deck]] skill produces the flashcard decks these words come from.
