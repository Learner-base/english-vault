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

### Hard-words focus (this is a spelling drill, not a vocab dump)
The deck deliberately targets the words people actually misspell, so `build.py`:
- **Tags each word** with the spelling trap(s) it exercises via `tag_word()` — codes
  `sc` (S vs C), `th`, `ph`, `ough`, `silent`, `double`, `british`, `vowel`. Tags ride on
  each word object as `tags[]` and drive the page's "focus on a pattern" tabs.
- **Adds a `CURATED` list** of classic English spelling-demons (accommodate, rhythm,
  conscience, queue…) plus any words the user names, so the deck isn't limited to the
  collected vocab. Curated `tags` are merged with the auto-classifier; curated words absent
  from the vocab are injected (`src:"curated"`).
- **Drops easy words** (`is_easy()`): scraping junk (`JUNK`), length ≤ 3, untagged
  4-letter words, and an `EASY` stoplist of common regular words. This is the *moderate*
  filter — it removes the obviously-simple words but keeps the substance; tighten `is_easy`
  if the user wants a smaller, tags-only pool.

To change which patterns exist, edit `TAG_ORDER` + `tag_word()` (and the `TAG_LABELS` map
and `#focusSwitch` buttons in the `PAGE` string must mirror them).

## How to build
```
python .claude/skills/dictation/scripts/build.py --repo-root . \
    --out generated/dictation/dictation.html
```
Re-run it any time the vocab files change — the word pool is regenerated and re-embedded.
Output goes to `generated/dictation/` (all generated artifacts live under `generated/`,
never in `vocab/`).

**Then refresh the main page** so the new/updated file shows in the main page `dev/index.html`
file browser:
```
python3 dev/scripts/build_index.py
```

## What the page does (features)
- **Text-to-speech** via the Web Speech API (`en-GB` voice, "Speak slowly" toggle at 0.6×).
- **Focus on a spelling pattern**: All hard / S·C / TH / PH / -ough / Silent / Double /
  British — filters the pool to words carrying that tag (combines with the source filter).
- **Sources**: All words / Learning-only / My mistakes (words previously misspelled).
- **Session length**: 15 / 30 / 50 / All, optional shuffle. The pool counter updates live
  to show how many words match the current focus + source.
- **On correct**: green ✓, mark word mastered, show meaning hint + "Why it's tricky" chips
  (the word's spelling-trap tags).
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
