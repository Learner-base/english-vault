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
import argparse, json, os


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
               "  .related{font-size:13.5px;color:var(--ink-2);margin:2px 0 14px}\n"
               "  .related .lab{font-family:var(--mono);font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--ink-3);display:block;margin-bottom:7px}\n"
               "  .related .tag{font-family:var(--serif)}\n  ")
    tpl = rep(tpl, "  .acc{border-top:1px solid var(--line-2)}",
              "  " + css_add + ".acc{border-top:1px solid var(--line-2)}")

    old_front = ('front=`<div class="pos">${v.pos}</div><div class="word">${esc(v.w)}</div>'
                 '${v.ipa?`<div class="ipa">${esc(v.ipa)}</div>`:""}${speakBtn(v.w)}'
                 '<div class="hint">tap to reveal the meaning</div>`;')
    new_front = ('front=`<div class="pos">${v.pos}</div><div class="word">${esc(v.w)}</div>'
                 '${v.form&&v.form!==v.w?`<div class="form-front">${esc(v.form)}</div>`:""}'
                 '${v.ipa?`<div class="ipa">${esc(v.ipa)}</div>`:""}${speakBtn(v.w)}'
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
    return tpl


def update_learning(path, set_name, cards):
    data = {}
    if os.path.exists(path):
        try: data = json.load(open(path))
        except Exception: data = {}
    if not isinstance(data, dict): data = {}
    data[set_name] = cards
    json.dump(data, open(path, "w"), ensure_ascii=False, indent=2)


def update_known(path, set_name, words, heading_note=""):
    header = ("# Known words\n\n"
              "Words already seen in processed reading passages & questions. "
              "Do NOT regenerate vocab cards for these.\n\n")
    body = open(path).read() if os.path.exists(path) else header
    if not body.startswith("# Known words"):
        body = header + body
    marker = "## %s" % set_name
    block = "%s%s\n\n%s\n" % (marker, (" " + heading_note if heading_note else ""), " ".join(words))
    if marker in body:
        start = body.index(marker)
        nxt = body.find("\n## ", start + 1)
        end = nxt if nxt != -1 else len(body)
        body = body[:start] + block + ("\n" + body[end:].lstrip("\n") if nxt != -1 else "")
    else:
        body = body.rstrip() + "\n\n" + block
    open(path, "w").write(body)


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
    update_known(os.path.join(root, "vocab/known.md"), a.set_name, known, a.heading_note)

    print("HTML       :", out, "(%d cards, %d structures)" % (len(deck["vocab"]), len(deck["structures"])))
    print("learning.json: key '%s' updated" % a.set_name)
    print("known.md   : section '%s' updated (%d words)" % (a.set_name, len(known)))


if __name__ == "__main__":
    main()
