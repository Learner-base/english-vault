#!/usr/bin/env python3
"""Retire a finished vocab deck.

For each deck given (an HTML path under generated/vocab/, or a bare set name):

1. git mv the deck HTML from generated/vocab/inprogress/ -> generated/vocab/done/
2. move that set's cards from vocab/learning.json -> vocab/need-to-review.json
3. rebuild index.html (scripts/build_index.py)

Set name = deck filename without the trailing "-vocabs.html"; it is the key used
in learning.json.
"""
import argparse
import collections
import json
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
INPROGRESS = os.path.join(ROOT, "generated/vocab/inprogress")
DONE = os.path.join(ROOT, "generated/vocab/done")
LEARNING = os.path.join(ROOT, "vocab/learning.json")
REVIEW = os.path.join(ROOT, "vocab/need-to-review.json")


def load(path):
    if not os.path.exists(path):
        return collections.OrderedDict()
    with open(path, encoding="utf-8") as f:
        return json.load(f, object_pairs_hook=collections.OrderedDict)


def save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def resolve(target):
    """target -> (set_name, source html path or None)"""
    name = os.path.basename(target)
    if name.endswith(".html"):
        set_name = name[:-len(".html")]
        if set_name.endswith("-vocabs"):
            set_name = set_name[:-len("-vocabs")]
    else:
        set_name = name
        name = set_name + "-vocabs.html"
    for cand in (os.path.join(INPROGRESS, name),
                 os.path.abspath(target) if target.endswith(".html") else None):
        if cand and os.path.exists(cand):
            return set_name, cand
    if os.path.exists(os.path.join(DONE, name)):
        return set_name, None  # already in done/
    return set_name, None


def move_html(src, set_name):
    if src is None:
        print("  html: already in done/ (or not found) — skipped")
        return
    os.makedirs(DONE, exist_ok=True)
    dst = os.path.join(DONE, os.path.basename(src))
    if subprocess.call(["git", "mv", src, dst], cwd=ROOT) != 0:
        os.replace(src, dst)
    print("  html: %s -> %s" % (os.path.relpath(src, ROOT), os.path.relpath(dst, ROOT)))


def move_cards(set_name):
    learning, review = load(LEARNING), load(REVIEW)
    cards = learning.pop(set_name, None)
    if cards is None:
        print("  cards: no '%s' key in learning.json — skipped" % set_name)
        return 0
    existing = review.get(set_name, [])
    seen = {c.get("w") for c in existing}
    merged = existing + [c for c in cards if c.get("w") not in seen]
    review[set_name] = merged
    save(REVIEW, review)
    save(LEARNING, learning)
    print("  cards: %d word(s) moved to need-to-review.json under '%s'"
          % (len(cards), set_name))
    return len(cards)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("decks", nargs="+",
                    help="deck HTML path or bare set name (e.g. C20-r1)")
    ap.add_argument("--no-index", action="store_true",
                    help="skip the index.html rebuild")
    a = ap.parse_args()

    for target in a.decks:
        set_name, src = resolve(target)
        print("%s:" % set_name)
        move_html(src, set_name)
        move_cards(set_name)

    if a.no_index:
        return 0
    return subprocess.call([sys.executable, os.path.join(ROOT, "scripts/build_index.py")],
                           cwd=ROOT)


if __name__ == "__main__":
    sys.exit(main())
