#!/usr/bin/env python3
"""Assemble a vocab study deck HTML from templates/vocab.html and update the
project's learning.json and known.md.

The base template (templates/vocab.html) has NO `form` line on the card front and
NO "related expressions" block. This script injects the deck data AND patches the
render code + CSS to add those two features, so a plain template stays reusable.

Usage:
    python build.py \
        --deck deck.json \
        --set-name cambridge-21-reading-3 \
        --title "Cambridge 21 · Reading Test 3" \
        --eyebrow "Cambridge IELTS 21 · Reading Test 3" \
        --lede "Unknown vocabulary and sentence patterns from ..." \
        --key study_cam21_reading3_v1 \
        --out vocab/cambridge-21-reading-3-vocabs.html \
        --known-words known_words.txt \
        --repo-root .

deck.json shape: {"vocab": [ {card}, ... ], "structures": [ {structure}, ... ]}
  card fields: w, form, pos, ipa, forms, def, uz, senses[], ex, syn[], ant[], related[]
"""
import argparse, json, os, re


def rep(s, old, new, n=1):
    if s.count(old) < n:
        raise SystemExit("Template string not found (template changed?):\n  " + old[:90])
    return s.replace(old, new, n)


def replace_array(s, decl, payload):
    i = s.index(decl)
    j = s.index("];", i) + 2
    return s[:i] + decl.split("=")[0].strip() + " = " + payload + ";" + s[j:]


def build_html(tpl, deck, title, eyebrow, lede, key):
    tpl = replace_array(tpl, "const VOCAB = [", json.dumps(deck["vocab"], ensure_ascii=False))
    tpl = replace_array(tpl, "const STRUCTURES = [", json.dumps(deck["structures"], ensure_ascii=False))

    tpl = rep(tpl, "<title>The World of Sugar — Vocabulary & Structures</title>",
              "<title>%s — Vocabulary & Structures</title>" % title)
    tpl = rep(tpl, '<div class="eyebrow">Reading · The World of Sugar</div>',
              '<div class="eyebrow">%s</div>' % eyebrow)
    tpl = rep(tpl,
              '<p class="lede">B2+ vocabulary and sentence patterns drawn from the book review of Ulbe Bosma\'s The World of Sugar.</p>',
              '<p class="lede">%s</p>' % lede)
    tpl = rep(tpl, 'const KEY="study_world_of_sugar_v1";', 'const KEY="%s";' % key)

    css_add = (".front .form-front{font-family:var(--serif);font-style:italic;font-size:16.5px;color:var(--ink-2);margin-top:9px;line-height:1.3;max-width:30ch}\n"
               "  .front .hintbtn{margin-top:12px;border:1px dashed var(--line);background:transparent;color:var(--ink-3);border-radius:999px;padding:6px 14px;font-family:var(--mono);font-size:11px;letter-spacing:.06em;text-transform:uppercase;cursor:pointer}\n"
               "  .front .hintbtn:hover{border-color:var(--ink-2);color:var(--ink-2)}\n"
               "  .related{font-size:13.5px;color:var(--ink-2);margin:2px 0 14px}\n"
               "  .related .lab{font-family:var(--mono);font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--ink-3);display:block;margin-bottom:7px}\n"
               "  .related .tag{font-family:var(--serif)}\n"
               "  .mnem .kw,.mnem .tr{font-family:var(--mono);font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--ink-3);display:block;margin-bottom:5px}\n"
               "  .mnem .kw b,.mnem .tr b{color:var(--ink);text-transform:none;font-size:14px;letter-spacing:0}\n"
               "  .mnem .story{font-family:var(--serif);font-style:italic;font-size:15px;line-height:1.55;margin:8px 0 0;padding-top:8px;border-top:1px dashed var(--line)}\n  ")
    tpl = rep(tpl, "  .acc{border-top:1px solid var(--line-2)}",
              "  " + css_add + ".acc{border-top:1px solid var(--line-2)}")

    old_front = ('front=`<div class="pos">${v.pos}</div><div class="word">${esc(v.w)}</div>'
                 '${v.ipa?`<div class="ipa">${esc(v.ipa)}</div>`:""}${speakBtn(v.w)}'
                 '<div class="hint">tap to reveal the meaning</div>`;')
    # Hide the `form` hint (e.g. "shiny aubergines") behind a "Show hint" button on
    # the front; revealing it swaps the button for the italic form text and reflows.
    new_front = ('front=`<div class="pos">${v.pos}</div><div class="word">${esc(v.w)}</div>'
                 + "${v.form&&v.form!==v.w?`<button class=\"hintbtn\" onclick=\"event.stopPropagation();this.classList.add('hidden');this.nextElementSibling.classList.remove('hidden');fitCard()\">Show hint</button><div class=\"form-front hidden\">${esc(v.form)}</div>`:\"\"}"
                 + '${v.ipa?`<div class="ipa">${esc(v.ipa)}</div>`:""}${speakBtn(v.w)}'
                 '<div class="hint">tap to reveal the meaning</div>`;')
    tpl = rep(tpl, old_front, new_front)

    old_senses = ('${v.senses&&v.senses.length?`<p class="senses"><span class="lab">also means</span>'
                  '${v.senses.map(esc).join("; ")}</p>`:""}\n'
                  '    <p class="forms">${esc(v.forms)}</p>')
    new_senses = ('${v.senses&&v.senses.length?`<p class="senses"><span class="lab">also means</span>'
                  '${v.senses.map(esc).join("; ")}</p>`:""}\n'
                  '    ${v.related&&v.related.length?`<p class="related"><span class="lab">related expressions</span>${tags(v.related)}</p>`:""}\n'
                  '    <p class="forms">${esc(v.forms)}</p>')
    tpl = rep(tpl, old_senses, new_senses)

    # Inject an optional mnemonic accordion as the FIRST accordion on the card back
    # (keyword-mnemonic memory aid). Only renders when the card has a `mnem` field,
    # so decks built without mnemonics are unaffected.
    old_ex_acc = '    ${acc("Example — from the passage",`<em>${esc(v.ex)}</em>`)}'
    new_ex_acc = ('    ${v.mnem?acc("Yodlash uchun \\u2014 keyword",'
                  '`<div class="mnem"><span class="kw">Keyword: <b>${esc(v.mnem.kw)}</b></span>'
                  '${v.uz?`<span class="tr">Tarjima: <b>${esc(v.uz)}</b></span>`:""}'
                  '<p class="story">${esc(v.mnem.story)}</p></div>`):""}\n'
                  '    ${acc("Example — from the passage",`<em>${esc(v.ex)}</em>`)}')
    tpl = rep(tpl, old_ex_acc, new_ex_acc)
    return tpl


def update_learning(path, set_name, cards):
    data = {}
    if os.path.exists(path):
        try: data = json.load(open(path))
        except Exception: data = {}
    if not isinstance(data, dict): data = {}
    data[set_name] = cards
    json.dump(data, open(path, "w"), ensure_ascii=False, indent=2)


def update_known(path, words):
    """known.md holds words only, grouped A–Z under `## <LETTER>` headings, each
    group a sorted space-separated line. Easy to look a word up by its first letter.
    Merge new words in, dedupe, rewrite."""
    existing = []
    if os.path.exists(path):
        for line in open(path).read().splitlines():
            if line.startswith("#"):   # drop title + `## <LETTER>` headings
                continue
            existing += line.split()
    clean = set()
    for w in existing + list(words):
        w = w.lower().strip(".,;:!?()[]\"'")   # strip surrounding punctuation
        if re.fullmatch(r"[a-z][a-z'-]*", w):  # keep only real word tokens
            clean.add(w)
    groups = {}
    for w in sorted(clean):
        groups.setdefault(w[0].upper(), []).append(w)
    out = "# Known words\n"
    for letter in sorted(groups):
        out += "\n## %s\n%s\n" % (letter, " ".join(groups[letter]))
    open(path, "w").write(out)


def remove_from_general_unknown(path, cards):
    """general-unknown.md is a SOURCE of loose unknown words (`- word => sentence`),
    NOT a sink. Once a word has been turned into a card in a generated deck it is
    "handled", so drop its bullet from the file. Match a bullet's leading label (the
    text before the first `=`) against the deck's card words, by full label or first
    token, case-insensitively. build.py never ADDS to this file."""
    if not os.path.exists(path):
        return 0
    words = set()
    for c in cards:
        w = str(c.get("w", "")).strip().lower()
        if w:
            words.add(w)
    kept, removed = [], 0
    for ln in open(path).read().splitlines():
        m = re.match(r"\s*-\s+(.*)", ln)
        if m and m.group(1).strip():
            label = m.group(1).split("=")[0].strip().lower()
            first = label.split()[0] if label.split() else ""
            if label in words or first in words:
                removed += 1
                continue
        kept.append(ln)
    open(path, "w").write("\n".join(kept) + "\n")
    return removed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--deck", required=True)
    ap.add_argument("--set-name", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--eyebrow", required=True)
    ap.add_argument("--lede", required=True)
    ap.add_argument("--key", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--known-words", required=True, help="file with newline/space separated words")
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--heading-note", default="")
    a = ap.parse_args()

    root = a.repo_root
    tpl = open(os.path.join(root, "templates/vocab.html")).read()
    deck = json.load(open(a.deck))
    ws = [x["w"] for x in deck["vocab"]]
    dupes = sorted({w for w in ws if ws.count(w) > 1})
    if dupes:
        raise SystemExit("Duplicate base words in deck (dedupe first): %s" % dupes)

    html = build_html(tpl, deck, a.title, a.eyebrow, a.lede, a.key)
    out = a.out if os.path.isabs(a.out) else os.path.join(root, a.out)
    # Generated HTML belongs under generated/, not in the data folder vocab/.
    parts = os.path.normpath(out).split(os.sep)
    if "vocab" in parts and "generated" not in parts:
        raise SystemExit("Refusing to write generated HTML into vocab/. Use --out generated/vocab/<name>.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w").write(html)

    known = [w for w in open(a.known_words).read().replace("\n", " ").split(" ") if w]
    update_learning(os.path.join(root, "vocab/learning.json"), a.set_name, deck["vocab"])
    update_known(os.path.join(root, "vocab/known.md"), known)
    removed_gen = remove_from_general_unknown(os.path.join(root, "vocab/general-unknown.md"), deck["vocab"])

    print("HTML       :", out, "(%d cards, %d structures)" % (len(deck["vocab"]), len(deck["structures"])))
    print("learning.json: key '%s' updated" % a.set_name)
    print("known.md   : flat word list updated (+%d words this run)" % len(known))
    print("general-unknown.md: -%d handled words removed" % removed_gen)


if __name__ == "__main__":
    main()
