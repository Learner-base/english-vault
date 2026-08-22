# -*- coding: utf-8 -*-
"""Refresh the baked-in VOCAB array of a generated deck page from the vocab store.

The deck pages carry their cards inline. When a field is added to the store
(formUz), the page keeps serving the old array. Rebuilding the whole page is not
an option for C20-r1: it carries a hand-written passage glossary that no
generator can reproduce. So swap just the array, leaving every other byte alone.
"""
import io, json, os, re, sys

ROOT = os.path.dirname(os.path.abspath(__file__))


def sync(page, cards):
    s = io.open(page, encoding="utf-8").read()
    m = re.search(r"const VOCAB = (\[.*?\]);\n", s, re.S)
    if not m:
        return None
    old = json.loads(m.group(1))
    by_w = {str(c.get("w", "")): c for c in cards}
    out, changed = [], 0
    for c in old:
        fresh = by_w.get(str(c.get("w", "")))
        if fresh and fresh != c:
            out.append(fresh)
            changed += 1
        else:
            out.append(c)
    new = json.dumps(out, ensure_ascii=False)
    s = s[:m.start(1)] + new + s[m.end(1):]
    io.open(page, "w", encoding="utf-8").write(s)
    return changed, len(out)


if __name__ == "__main__":
    page, store, key = sys.argv[1], sys.argv[2], sys.argv[3]
    cards = json.load(io.open(store, encoding="utf-8"))[key]
    changed, total = sync(page, cards)
    print(f"{page}: {changed}/{total} cards refreshed from {store}[{key}]")
