---
name: keyword-mnemonics
description: Generate Keyword-Mnemonic memory aids for English vocabulary — link a word's English sound/spelling to a phonetically similar Uzbek word or globally-known term (brand/tech), then an absurd 1-sentence Uzbek story tying that keyword to the word's meaning. Use when building vocab cards (feeds the vocab-deck `mnem` field, rendered as an accordion on the card back) or whenever the user asks for a way to remember a word.
---

# Keyword Mnemonics Method

Make an English word stick by hooking its **sound** to something the learner already
knows, then wrapping both in a vivid, funny, slightly absurd mini-scene in Uzbek.

## Output shape (per word)
- **Translation** — exact Uzbek meaning (same as the card's `uz`).
- **Keyword** — an Uzbek word OR a globally-known term (brand/tech/name) that sounds
  like the English word or a chunk of it. Show the gloss in ( ) if helpful.
- **Story** — ONE Uzbek sentence, absurd/funny/vivid, that connects the **Keyword**
  to the **Translation** so recalling one pulls the other.

## Rules
1. **Sound first.** The keyword must be phonetically close to the English word (whole
   or a clear syllable): maze→*mayiz*, thrash→*trash*, interpret→*internet*.
2. **Easy to picture.** The story must be instantly imaginable and easy to remember —
   concrete objects and actions, no abstractions. Short. One sentence.
3. **Both halves present.** The sentence must contain the keyword idea AND the meaning,
   so the link is forced (not just a sentence using the word).
4. **Uzbek story, natural.** Write the story in natural Uzbek (apostrophes ok: o', g').
5. **Every card** gets one when mnemonics are enabled.
6. Keyword can be a combo: machinery → "Mashina + Eri" ("mashina eriyapti").

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
