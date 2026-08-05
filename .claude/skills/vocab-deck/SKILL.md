---
name: vocab-deck
description: Generate an IELTS vocabulary study deck (interactive HTML flashcards) from a reading-test HTML plus a user-pasted list of unknown words, then update vocab/learning.json and vocab/known.md. Use when the user shares a reading passage file and a list of unknown vocab/phrases and wants a vocab learning HTML built from templates/vocab.html.
---

# Vocab deck generator

Turn a reading test + a pasted list of unknown words into an interactive flashcard
HTML (flip / recall / cloze + sentence structures), and keep `learning.json` and
`known.md` in sync.

## Inputs (from the user)
- **Reading HTML** — a file under `reading/…` (passages + questions are embedded as
  `const testData = {...}` inside a `<script>`; the visible page text is NOT the source).
- **Unknown-word list** — the user always pastes it. Words/phrases, comma-separated.
  If the user later pastes a sentence or multi-word chunk, add cards for the useful
  words in it too.
- **Output file name** — e.g. `cambridge-21-reading-3-vocabs`. Derive a **set name**
  from it by dropping `-vocabs` (→ `cambridge-21-reading-3`).

## Hard rules (from the user)
1. **The user pastes the unknown list.** Do not auto-invent the vocab set. But **every
   other word** from the passages + questions must go into `known.md` (via `known_words.txt`)
   so it is never re-flagged in future runs.
2. **learning.json and known.md are updated on EVERY run** (both, always). `build.py` does this.
3. **Order:** question words first (in question order across all parts), then passage
   words (in passage order). Get each meaning from the **exact sentence** it appears in.
4. **Base words only.** The card's `w` is the base/lemma (e.g. `pose`, not "posed by").
   Put the inflected form(s)/phrase actually used in the passage in `form` — it renders
   in italics under the word on the card front.
5. **Related expressions inside the card.** Collocations/chunks the user cares about
   (e.g. "legacy of the colonial government", "relatively uplifting", "on an industrial
   scale", "as opposed to") go in `related[]`.
6. **Dedupe.** Merge different inflections of the same base into ONE card (swollen/swells →
   `swell`; posed by/poses → `pose`; steppes/steppe → `steppe`). If the user pastes the same
   word twice, keep one. `build.py` aborts if two cards share a base `w`.
7. If a listed word is **not** in the passage text, still include it (user asked), use a
   faithful paraphrase example, and note the passage's actual wording in `senses[]`.

## Card schema (`deck.json` → `vocab[]`)
```
w        base word / lemma (unique across the deck; also the localStorage progress key)
form     inflected form(s) or phrase from the passage, shown under the word (e.g. "posed by · poses")
pos      part of speech: noun / verb / adjective / adverb / phrase / preposition …
ipa      "/…/"  British IPA
forms    "pose · posed · posing"  (word family, middot-separated)
def      meaning IN THIS CONTEXT (from the exact sentence), one clear B1-level line
uz       Uzbek translation (may use apostrophes: o'zbek, yo'q)
senses   [ other common meanings ]  (empty [] if none)
ex       the EXACT sentence from the passage (from readable.txt)
syn      [ 2–3 context synonyms ]
ant      [ antonyms ]  (empty [] if none)
related  [ collocations / phrase chunks to learn alongside ]
```

## Structures (`deck.json` → `structures[]`)
Keep the Structures section. Draw ~10–12 real sentence patterns from the passages:
```
name     short label of the pattern (e.g. "Despite + noun, ...")
pattern  the abstract shape (e.g. "Despite + [noun], + [main clause]")
use      when/why to use it, 1–2 lines
ex       the exact passage sentence using it
mark     [ substrings of ex to highlight ]
extra    one fresh example of your own
```

## Steps
1. **Extract** the passage + words:
   ```
   python .claude/skills/vocab-deck/scripts/extract.py "<reading.html>" <scratch_dir>
   ```
   → `readable.txt` (exact sentences), `known_words.txt` (all passage+question words).
2. **Read `readable.txt`** to get exact example sentences and confirm which listed words
   are present. Grep it (Python, not zsh) to pull the sentence for each word.
3. **Author the deck** in a Python builder (double-quoted strings so Uzbek apostrophes are
   safe), following the schema, rules, and ordering above. Dump to `deck.json`:
   ```python
   # build_cards.py  →  json.dump({"vocab": CARDS, "structures": STRUCTURES}, open("deck.json","w"), ensure_ascii=False)
   ```
4. **Build** everything:
   ```
   python .claude/skills/vocab-deck/scripts/build.py \
     --deck <scratch>/deck.json --set-name <set> \
     --title "<Human Title>" --eyebrow "<Eyebrow line>" \
     --lede "<one-sentence intro>" --key study_<slug>_v1 \
     --out vocab/<name>-vocabs.html --known-words <scratch>/known_words.txt --repo-root .
   ```
   This writes the HTML, keys `learning.json` by `<set>`, and adds a `## <set>` section to `known.md`.
5. **Verify** (no browser needed): the script's `<script>` must parse.
   ```
   node -e "const fs=require('fs');const h=fs.readFileSync('vocab/<name>-vocabs.html','utf8');new Function(h.match(/<script>([\s\S]*)<\/script>/)[1]);console.log('OK')"
   ```
   Optionally serve `vocab/` on `127.0.0.1` (not `localhost` — the browser may use IPv6)
   and screenshot to eyeball the front `form` line, flip, and related chips.
6. **Report**: counts, the three files touched, and note words that weren't in the passage.

## Notes
- The base `templates/vocab.html` intentionally lacks the front-`form` line and the
  `related` block; `build.py` patches them in every build. If the template's markup changes,
  `build.py` fails loudly with the missing string — update the patch strings then.
- Scratch files (readable.txt, deck.json, etc.) belong in the session scratchpad, not the repo.
