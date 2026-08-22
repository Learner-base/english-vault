---
name: translate-practice
description: Maintain the translation-practice page — difficult sentences from finished reading passages and listening scripts, each with an Uzbek translation, shown in groups of 20 with a "Show translation" button. Use when a passage/test is finished (moved to done) and its hard sentences should be added, when the user asks to add or fix translation sentences, or to rebuild generated/translate/translate.html.
---

# Translation practice

A study page that shows **difficult English sentences** (from finished reading
passages and listening scripts) and, on demand, their **Uzbek translation**.

## How it works

- The single source of truth is **`vocab/translations.json`** — a JSON array of
  `{ "en", "uz", "src", "type" }`:
  - `en` — the English sentence (exact).
  - `uz` — its Uzbek translation.
  - `src` — a short label, e.g. `"C21-r1 · The Davies Sisters"` or `"C21-l1 · Listening script"`.
  - `type` — `"reading"` or `"listening"` (drives the badge + the Source filter).
- **`scripts/build_translate.py`** renders that store into
  `generated/translate/translate.html`: a light blue-gradient page with a
  Reading / Listening filter, a **group-of-20** picker, and a per-sentence
  **Show translation** toggle. It is called automatically from
  `dev/scripts/build_index.py`, so the page updates on every rebuild.

## Add sentences when a passage/test is finished

The page should **grow each time a passage moves to done** (see
[move-to-done](../move-to-done/SKILL.md)). After finishing a test:

1. Read the finished passage / listening script.
2. Pick the **difficult** sentences — the long, syntactically complex, or
   vocabulary-heavy ones a learner would struggle with (a handful per passage,
   e.g. ~6; don't dump every sentence).
3. Translate each into natural Uzbek (don't machine-translate blindly; keep it
   fluent and faithful).
4. Append them to `vocab/translations.json` with the right `src` and `type`.
   Keep existing entries — the store is cumulative and deduped by sentence.
5. Rebuild:
   ```
   python3 dev/scripts/build_index.py
   ```
6. **Commit** with the user's go-ahead; do not push unless asked.

## Notes

- Reading passages from the reading-generate template expose their text in
  `const TEST.passages[].body[]`; imported tests may only have the text in the
  DOM — grab it from the rendered page if needed.
- Listening sentences come from the transcript / audioscript of a finished
  listening test.
- Keep sentences as **whole sentences** (not fragments) so the translation makes
  sense on its own.
