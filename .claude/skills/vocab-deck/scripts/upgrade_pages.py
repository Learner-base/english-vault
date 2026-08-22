#!/usr/bin/env python3
"""Bring an already-generated vocab deck page up to date with the current template.

Deck pages are generated once from a deck JSON that is not kept, and at least one
of them (C20-r1) carries a hand-written passage glossary no generator reproduces.
So a page cannot simply be rebuilt — new template features have to be patched into
the page that already exists.

This adds the **whole-phrase panel**: the passage highlights a collocation
("vary quite a bit") but the card only translates the head word ("quite a bit"),
so an accordion at the foot of the card back translates the phrase as a unit.
It needs `formUz` on the card, which `sync_cards.py` copies in from the store.

Idempotent — a page that already has the panel is left alone.

    python3 .claude/skills/vocab-deck/scripts/upgrade_pages.py                 # every deck page
    python3 .claude/skills/vocab-deck/scripts/upgrade_pages.py <file.html> …   # named pages
"""
import glob
import importlib.util
import io
import os
import re
import sys

sys.dont_write_bytecode = True

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
PAGES = "generated/vocab/*/*.html"

_spec = importlib.util.spec_from_file_location(
    "vocab_build", os.path.join(ROOT, ".claude/skills/vocab-deck/scripts/build.py"))
_vb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_vb)


def pieces():
    """The CSS and the helper exactly as the builder emits them today."""
    tpl = io.open(os.path.join(ROOT, "dev/templates/vocab.html"), encoding="utf-8").read()
    built = _vb.build_html(tpl, {"vocab": [], "structures": []}, "t", "e", "l", "k")
    css = re.search(r"\n(  \.acc\.phrase\{.*?)\n  \.acc\{", built, re.S)
    fn = re.search(r"(function phraseAcc\(v\)\{.*?\n\})\n", built, re.S)
    if not css or not fn:
        raise SystemExit("build.py no longer emits the phrase panel — upgrade_pages is stale")
    return css.group(1), fn.group(1)


def upgrade(path, css, fn):
    s = io.open(path, encoding="utf-8").read()
    if "phraseAcc" in s:
        return "already up to date"
    if "function tags(a){" not in s or "${acc(\"Antonyms\",tags(v.ant))}" not in s:
        return "SKIPPED — not a deck page built from the vocab template"
    s = s.replace("  .acc{border-top:1px solid var(--line-2)}",
                  css + "\n  .acc{border-top:1px solid var(--line-2)}", 1)
    s = s.replace("function tags(a){", fn + "\nfunction tags(a){", 1)
    s = s.replace('    ${acc("Antonyms",tags(v.ant))}\n  `;',
                  '    ${acc("Antonyms",tags(v.ant))}\n    ${phraseAcc(v)}\n  `;', 1)
    io.open(path, "w", encoding="utf-8").write(s)
    return "phrase panel added"


def main():
    css, fn = pieces()
    targets = sys.argv[1:] or sorted(glob.glob(os.path.join(ROOT, PAGES)))
    for t in targets:
        p = t if os.path.isabs(t) else os.path.join(ROOT, t)
        print(f"{os.path.relpath(p, ROOT)}: {upgrade(p, css, fn)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
