#!/usr/bin/env python3
"""Regenerate /progress.html — what I'm studying right now, newest first.

The page used to be hand-written and went stale the moment a deck was generated
or retired. It is now built from the file tree:

  * **generated/vocab** — the decks still in `inprogress/`,
  * **to review**       — the decks in `review/` (retired, words still in
    vocab/need-to-review.json),
  * **practice pages**  — dictation and translation.

Inside every group the **most recently added file comes first** (git tells us
when each file first appeared; anything not yet committed counts as newest), and
that first item is highlighted with a `now` badge — so the deck you just made is
always the one the page points at.

**Pinning beats recency.** Files named in `vocab/studying-now.md` are held at the
top of their group with the badge, however many newer files appear afterwards.
That list is the answer to "this is what I'm on right now"; without it the badge
would move to whatever was generated last.

Run it after adding or retiring anything:
    python3 dev/scripts/build_progress.py
    python3 dev/scripts/build_progress.py --pin C20-r1-vocabs.html
    python3 dev/scripts/build_progress.py --unpin C20-r1-vocabs.html
    python3 dev/scripts/build_progress.py --list
It is also called at the end of dev/scripts/build_index.py.
"""
import os, sys, subprocess, html

# scripts/ lives in dev/, so the site root is two levels up.
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "dev", "progress.html")

# (folder, heading, sub-heading, auto-badge?)
# auto-badge means "if nothing here is pinned, highlight the newest one". The
# drills are always-available tools rather than something you work through, so
# they are only highlighted when you pin one yourself.
GROUPS = [
    ("generated/vocab/inprogress", "generated/vocab/inprogress", "Still learning", True),
    ("generated/vocab/review", "generated/vocab/review", "To review", True),
    ("practice",               "practice pages",         "Drills", False),
]
PRACTICE = ["generated/dictation/dictation.html", "generated/translate/translate.html"]
PINS = os.path.join(ROOT, "vocab", "studying-now.md")


def load_pins():
    """Bare file names pinned to the top of their group, in listed order."""
    if not os.path.exists(PINS):
        return []
    out = []
    for line in open(PINS, encoding="utf-8"):
        t = line.strip()
        if not t or t.startswith("#"):
            continue
        if t.startswith("- ") or t.startswith("* "):
            t = t[2:].strip()
        elif "/" not in t and not t.endswith(".html"):
            continue          # prose in the file's header, not a file name
        if t.endswith(".html"):
            out.append(os.path.basename(t))
    return out


def save_pins(names):
    """Rewrite the list, keeping whatever header prose the file already has."""
    header = []
    if os.path.exists(PINS):
        for line in open(PINS, encoding="utf-8"):
            t = line.strip()
            if t.startswith(("- ", "* ")) and t.endswith(".html"):
                continue
            header.append(line.rstrip("\n"))
        while header and not header[-1].strip():
            header.pop()
    else:
        header = ["# Studying now", "",
                  "Files pinned to the top of progress.html, with the `now` badge.",
                  "One file name per line."]
    body = "\n".join(header) + "\n\n" + "".join(f"- {n}\n" for n in names)
    with open(PINS, "w", encoding="utf-8") as f:
        f.write(body)


def pin(name, on=True):
    """Add or remove one file. Returns True when the list actually changed."""
    name = os.path.basename(name.strip())
    names = load_pins()
    if on and name not in names:
        names.append(name)
    elif not on and name in names:
        names.remove(name)
    else:
        return False
    save_pins(names)
    return True


def added_time(rel):
    """When this file first appeared, as a unix timestamp.

    Asked per file with --follow, because these files get moved around
    (inprogress/ → done/, and the whole dev/ reorg). A plain
    `git log --diff-filter=A --name-only` reports a moved file under its OLD
    path, so every deck would look equally old and fall back to alphabetical
    order — which silently put the wrong deck on top.

    A file git has never seen is brand new: fall back to its mtime.
    """
    try:
        out = subprocess.check_output(
            ["git", "log", "--diff-filter=A", "--follow", "--format=%ct", "-1", "--", rel],
            cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
        if out:
            return int(out.splitlines()[0])
    except Exception:
        pass
    try:
        return int(os.path.getmtime(os.path.join(ROOT, rel)))
    except OSError:
        return 0


def newest_first(paths, rank, pins=()):
    """Pinned files first (in the order listed), then newest, then alphabetical."""
    pins = list(pins)

    def key(p):
        n = os.path.basename(p)
        return (0, pins.index(n)) if n in pins else (1, 0), -rank.get(p, 0), p

    return sorted(paths, key=key)


def ranks_for(paths):
    return {p: added_time(p) for p in paths}


def collect():
    pins = load_pins()
    groups = []
    for key, label, sub, auto in GROUPS:
        if key == "practice":
            found = [p for p in PRACTICE if os.path.exists(os.path.join(ROOT, p))]
        else:
            d = os.path.join(ROOT, key)
            found = ([f"{key}/{f}" for f in os.listdir(d)
                      if f.endswith(".html") and not f.startswith(".")]
                     if os.path.isdir(d) else [])
        items = newest_first(found, ranks_for(found), pins)
        if items:
            groups.append((label, sub, items, auto))
    return groups


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>English Vault — In progress</title>
<style>
  :root{
    --bg:#f5f8fd;--card:#FFFFFF;--ink:#0f172a;--ink-2:#475569;--ink-3:#8a94a6;
    --line:#e6eaf1;--line-2:#eef2f8;--soft:#eff4fb;
    --blue:#1e6de6;--blue2:#3b82f6;--blued:#0f2f66;--bluebg:#eff6ff;
    --sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
    --mono:ui-monospace,"SF Mono",Menlo,Consolas,monospace;
  }
  *{box-sizing:border-box}html,body{margin:0;padding:0}
  body{background:var(--bg);color:var(--ink);font-family:var(--sans);line-height:1.55;-webkit-font-smoothing:antialiased}
  .wrap{max-width:720px;margin:0 auto;padding:22px 20px 90px}
  .hero{background:linear-gradient(135deg,#0f2f66,#1e6de6);color:#fff;border-radius:20px;
    padding:24px 24px 26px;box-shadow:0 14px 36px rgba(30,109,230,.24);margin-bottom:18px}
  .eyebrow{font-family:var(--mono);font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:#bfdbfe}
  h1{font-weight:800;font-size:29px;margin:8px 0 6px;letter-spacing:-.02em;color:#fff}
  .lede{color:#dbeafe;font-size:14.5px;margin:0}
  .home{display:inline-block;font-size:13px;font-weight:600;color:var(--blue);text-decoration:none;margin-bottom:18px}
  .home:hover{text-decoration:underline}
  .group{margin:0 0 14px;background:var(--card);border:1px solid var(--line);border-radius:14px;
    padding:14px 16px;box-shadow:0 1px 3px rgba(16,24,40,.05)}
  .group h2{font-family:var(--mono);font-size:12px;letter-spacing:.06em;color:var(--ink-3);text-transform:uppercase;margin:0 0 8px;padding-bottom:8px;border-bottom:1px solid var(--line-2);display:flex;justify-content:space-between;gap:10px}
  .group h2 .sub{font-family:var(--sans);letter-spacing:0;text-transform:none;color:var(--ink-3);font-weight:500}
  /* numbers are drawn with a counter, not the list marker: the highlighted row
     is a padded box, and a real marker sits outside it and gets lost */
  ol{margin:0;padding-left:0;list-style:none;counter-reset:item}
  li{counter-increment:item;margin:0;padding:5px 4px;font-size:14.5px;
    display:flex;align-items:baseline;gap:9px}
  li::before{content:counter(item) ".";flex:none;min-width:19px;text-align:right;
    font-family:var(--mono);font-size:12px;color:var(--ink-3)}
  li a{color:var(--ink);text-decoration:none;min-width:0;overflow-wrap:anywhere}
  li a:hover{color:var(--blue);text-decoration:underline}
  li.feat{padding:8px 10px;background:var(--bluebg);border:1px solid #d3e2fb;
    border-left:3px solid var(--blue);border-radius:8px}
  li.feat::before{color:var(--blue);font-weight:700}
  li.feat a{font-weight:700}
  li.feat .tag{font-family:var(--mono);font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:var(--blue);background:#dce9fc;padding:1px 7px;border-radius:999px;margin-left:auto;flex:none;align-self:center}
  .count{font-family:var(--mono);font-size:12px;color:var(--ink-3);margin-top:8px}
  .count b{color:var(--blue)}
</style>
</head>
<body>
<div class="wrap">
  <div class="hero">
    <div class="eyebrow">📈 English Vault</div>
    <h1>In progress</h1>
    <p class="lede">Things I'm currently working through — newest first, the latest one highlighted.</p>
  </div>
  <a class="home" href="./index.html">← All files</a>

__GROUPS__
  <div class="count">__COUNT__</div>
</div>
</body>
</html>
"""


def main():
    args = sys.argv[1:]
    if args and args[0] in ("--pin", "--unpin"):
        if len(args) < 2:
            print(f"usage: build_progress.py {args[0]} <file.html>")
            return
        on = args[0] == "--pin"
        for name in args[1:]:
            changed = pin(name, on)
            verb = "pinned" if on else "unpinned"
            print(f"{verb}: {os.path.basename(name)}"
                  + ("" if changed else "  (already there — no change)"))
        # fall through and regenerate, so the page is right straight away
    elif args and args[0] == "--list":
        names = load_pins()
        print("\n".join(f"- {n}" for n in names) if names else "(nothing pinned)")
        return

    pins = load_pins()
    groups, total = collect(), 0
    out = []
    for label, sub, items, auto in groups:
        total += len(items)
        # once something here is pinned, the newest-file badge would just be noise
        group_pinned = any(os.path.basename(r) in pins for r in items)
        rows = []
        for i, rel in enumerate(items):
            name = html.escape(os.path.basename(rel))
            href = html.escape("../" + rel, quote=True)
            # a pinned file always leads its group; otherwise the newest one
            # does, but only in the groups that ask for an automatic badge
            pinned = os.path.basename(rel) in pins
            lead = pinned or (auto and i == 0 and not group_pinned)
            cls = ' class="feat"' if lead else ""
            label_ = "pinned" if pinned else "now"
            tag = f'<span class="tag">{label_}</span>' if lead else ""
            rows.append(f'      <li{cls}><a href="{href}">{name}</a>{tag}</li>')
        out.append('  <div class="group">\n'
                   f'    <h2>{html.escape(label)}<span class="sub">{html.escape(sub)}</span></h2>\n'
                   "    <ol>\n" + "\n".join(rows) + "\n    </ol>\n  </div>\n")
    nlead = sum(r.count('class="feat"') for r in out)
    count = f"{total} items in progress"
    if nlead:
        count += f" · <b>{nlead}</b> highlighted"
    page = PAGE.replace("__GROUPS__", "\n".join(out)).replace("__COUNT__", count)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(page)
    npin = sum(1 for _, _, items, _a in groups
               for r in items if os.path.basename(r) in pins)
    print(f"Wrote {OUT}  ({total} items in {len(groups)} groups, "
          f"{npin} pinned, then newest first)")


if __name__ == "__main__":
    main()
