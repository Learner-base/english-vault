---
name: keyword-mnemonics
description: Generate Keyword-Mnemonic memory aids for English vocabulary — link a word's English sound/spelling to a phonetically similar Uzbek word or globally-known term (brand/tech), then an absurd 1-sentence Uzbek story tying that keyword to the word's meaning. Use when building vocab cards (feeds the vocab-deck `mnem` field, rendered as an accordion on the card back) or whenever the user asks for a way to remember a word.
---

# Keyword Mnemonics Method

Make an English word stick by hooking its **sound** to something the learner already
knows, then wrapping both in a vivid, funny, slightly absurd mini-scene in Uzbek.

## Output shape (per word)
- **Keyword** — an Uzbek word OR a globally-known term (brand/tech/name) that sounds
  like the English word or a chunk of it. Show the gloss in ( ) if helpful.
- **Translation** — exact Uzbek meaning (comes from the card's `uz`; the deck shows it
  inside the mnemonic accordion right under the keyword — ALWAYS present).
- **Story** — ONE Uzbek sentence, absurd/funny/vivid, that connects the **Keyword** to
  the **Translation** so recalling one pulls the other.

The card back renders all three together (Keyword → Tarjima → Story). Showing the
translation next to the keyword is deliberate: Atkinson & Raugh (1975) found learners
given the keyword **together with** the translation learned and retained more than
keyword alone.

## Best practices (research-backed — apply to EVERY card)
1. **Phonetic overlap, front-loaded.** The keyword should echo the START or the whole
   English word, not a buried syllable (maze→*mayiz*, sponge→*SpongeBob*, twitch→*Twitch*).
2. **Picturable + familiar keyword.** Pick something the learner can instantly see and
   already knows — a concrete object, a brand, a famous name. Never an abstract keyword.
3. **Interactive image.** Keyword and meaning must *do something to each other* in the
   sentence, not merely co-occur. The link is the memory, so force the interaction.
4. **Bizarre beats bland.** The more absurd/funny the scene, the better it sticks —
   exaggerate, break physics, make it silly. Keep it to ONE vivid sentence.
5. **Abstract words need extra work.** Verbs/adjectives/abstract nouns are harder to
   image — anchor them to a concrete mini-scene (an action someone performs) rather than
   a static picture.
6. **Bidirectional cue.** Put BOTH the keyword idea and the meaning in the sentence so it
   works seeing the word (→meaning) and, as far as possible, recalling the word.
7. **Professional, natural Uzbek.** Clean, natural phrasing (apostrophes ok: o', g').
   No broken grammar, no filler. One tight sentence.

## Operational
- **Every card** gets a mnemonic when mnemonics are enabled for the deck.
- Keyword may be a **combo** when one word can't carry the whole sound:
  machinery → "Mashina + Eri" ("mashina eriyapti").
- If no clean phonetic match exists (rare, e.g. *though*), pick the closest picturable
  sound and lean harder on a bizarre story — note it's an approximate hook.

## Examples (exact style/format)
- Word: Maze — Labirint / Chalg'ituvchi yo'laklar
  Keyword: Mayiz (Raisin)
  Story: "Labirint ichida adashib qolmaslik uchun yerga mayizlarni terib ketyapman."
- Word: Machinery — Mashina-uskunalar / Texnika
  Keyword: Mashina + Eri (machine melts)
  Story: "Zavoddagi eski mashina-uskunalar issiqdan erib, mashina eriyapti."
- Word: Interpret — Tarjima qilmoq / Izohlamoq
  Keyword: Internet
  Story: "Internet o'chib qolsa, chet ellikning gapini qanday tarjima qilishni bilmay qolaman."
- Word: Thrash — Kaltaklamoq / Savalamoq
  Keyword: Trash (Axlat)
  Story: "Ko'chadagi axlatni (trash) sochgan bezorini tutib olib, yaxshilab savashdi."

## Using it inside a vocab deck
When the user confirms mnemonics for a deck, add a `mnem` object to each card in
`deck.json`:
```
"mnem": { "kw": "Mayiz (Raisin)", "story": "Labirint ichida ... mayizlarni terib ketyapman." }
```
`build.py` renders it as the first accordion ("Yodlash uchun — keyword") on the card back.

## IMPORTANT — always ask first
Mnemonics are **opt-in per deck**. When generating a vocab deck, if the user has NOT
said whether they want mnemonics, ASK before building. Only add the `mnem` field / this
accordion if the user confirms. See [[vocab-deck]].
