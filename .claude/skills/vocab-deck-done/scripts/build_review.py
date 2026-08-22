#!/usr/bin/env python3
"""Generate the review decks in generated/vocab/review/ from vocab/need-to-review.json.

One page per set (`<set>-review.html`). The page is the normal vocab deck, plus a
SECOND hint on the card front: hint 1 is the collocation/form, hint 2 is the word's
example sentence with the word itself blanked out, so it stays a hint and not the
answer.

Run directly, or let `vocab_done.py` call it when a deck is retired.
"""
import argparse
import importlib.util
import json
import os
import re
import sys

sys.dont_write_bytecode = True   # don't litter the skills folder with __pycache__

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
REVIEW_JSON = os.path.join(ROOT, "vocab/need-to-review.json")
OUT_DIR = os.path.join(ROOT, "generated/vocab/review")

# Reuse the deck builder's template patching (front hint 1, related block, mnemonic).
_spec = importlib.util.spec_from_file_location(
    "vocab_build", os.path.join(ROOT, ".claude/skills/vocab-deck/scripts/build.py"))
_vb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_vb)

# --- the second hint -------------------------------------------------------
# JS helper: blank the target word out of the example sentence, same base-word
# match the cloze mode uses, so the sentence hints at the word without giving it.
MASK_JS = '''function maskEx(v){
  if(!v.ex) return "";
  const GAP='<span class="exgap">\\u2014\\u2014\\u2014</span>';
  const rx=s=>s.replace(/[.*+?^${}()|[\\]\\\\]/g,"\\\\$&");
  const words=String(v.w).trim().split(/\\s+/);
  let h=esc(v.ex);
  // multi-word entry: blank the whole phrase, allowing inflection on the last word
  if(words.length>1){
    const pat="\\\\b"+words.map(rx).join("\\\\s+")+"[a-z]*\\\\b";
    const re=new RegExp(pat,"ig");
    if(re.test(h)) return h.replace(new RegExp(pat,"ig"),GAP);
  }
  // single word (or phrase not found verbatim): blank the head word + its inflections
  const base=words[words.length>1?words.length-1:0].split("-")[0];
  let re=new RegExp("\\\\b"+rx(base)+"[a-z]*\\\\b","ig");
  if(!re.test(h)&&base.length>4&&/[ey]$/i.test(base)){
    // stem match, so dangle/dangling, enquiry/enquiries, cavity/cavities all blank out
    re=new RegExp("\\\\b"+rx(base.slice(0,-1))+"[a-z]*\\\\b","ig");
  }
  re.lastIndex=0;
  return h.replace(re,GAP);
}
'''

HINT2_CSS = (
    "  .front .ex-front{font-family:var(--serif);font-size:15.5px;line-height:1.5;"
    "color:var(--ink-2);margin-top:10px;max-width:34ch;text-align:center}\n"
    "  .front .ex-front .exgap{color:var(--ink-3);letter-spacing:.08em}\n"
)

HINT2_BTN = (
    "${v.ex?`<button class=\\\"hintbtn\\\" onclick=\\\"event.stopPropagation();"
    "this.classList.add('hidden');this.nextElementSibling.classList.remove('hidden');fitCard()\\\">"
    "Show example</button><div class=\\\"ex-front hidden\\\">${maskEx(v)}</div>`:\"\"}"
)

ANCHOR = '${v.ipa?`<div class="ipa">${esc(v.ipa)}</div>`:""}${speakBtn(v.w)}'


def build(cards, set_name, title, eyebrow, lede):
    tpl = open(os.path.join(ROOT, "dev/templates/vocab.html"), encoding="utf-8").read()
    html = _vb.build_html(tpl, {"vocab": cards, "structures": []},
                          title, eyebrow, lede, "review_%s_v1" % re.sub(r"\W+", "_", set_name))
    # second hint: button + masked example, right after hint 1 on the flip front
    html = _vb.rep(html, ANCHOR, HINT2_BTN + ANCHOR)
    html = _vb.rep(html, "function speakCurrent()", MASK_JS + "function speakCurrent()")
    html = _vb.rep(html, "  .acc{border-top:1px solid var(--line-2)}",
                   HINT2_CSS + "  .acc{border-top:1px solid var(--line-2)}")
    return html


def pretty(set_name):
    s = set_name.replace("-", " ")
    s = re.sub(r"\bcambridge (\d+)\b", r"Cambridge \1", s, flags=re.I)
    s = re.sub(r"\bC(\d+)\b", r"Cambridge \1", s)
    s = re.sub(r"\br(\d+)\b", r"Reading \1", s)
    s = re.sub(r"\btest (\d+)\b", r"Test \1", s, flags=re.I)
    s = re.sub(r"\breading (\d+)\b", r"Reading \1", s, flags=re.I)
    return s[:1].upper() + s[1:]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sets", nargs="*", help="set names to rebuild (default: all)")
    a = ap.parse_args()

    if not os.path.exists(REVIEW_JSON):
        print("review: no vocab/need-to-review.json — nothing to build")
        return 0
    data = json.load(open(REVIEW_JSON, encoding="utf-8"))
    wanted = a.sets or list(data)
    os.makedirs(OUT_DIR, exist_ok=True)

    for set_name in wanted:
        cards = data.get(set_name)
        if not cards:
            print("review: '%s' not in need-to-review.json — skipped" % set_name)
            continue
        name = pretty(set_name)
        html = build(cards, set_name,
                     "%s — Review" % name,
                     "Review · %s" % name,
                     "Words you have already studied in this set. Two hints on the front: "
                     "the collocation, then the example sentence with the word blanked out.")
        out = os.path.join(OUT_DIR, "%s-review.html" % set_name)
        open(out, "w", encoding="utf-8").write(html)
        print("review: %s (%d cards)" % (os.path.relpath(out, ROOT), len(cards)))

    # drop pages whose set is no longer under review
    for f in sorted(os.listdir(OUT_DIR)):
        if f.endswith("-review.html") and f[:-len("-review.html")] not in data:
            os.remove(os.path.join(OUT_DIR, f))
            print("review: removed stale %s" % f)
    return 0


if __name__ == "__main__":
    sys.exit(main())
