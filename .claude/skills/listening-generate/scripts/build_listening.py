#!/usr/bin/env python3
"""Assemble a Cambridge-style interactive IELTS Listening test HTML from a data.js.

Splices the three data objects (TEST / EXPL / answerHighlightQuotes) plus an AUDIO
array into templates/listening.html, embeds the section audio as base64 data: URIs,
optionally embeds a map/diagram image, verifies every highlight quote occurs in the
transcript, runs `node --check`, and writes the final self-contained file.

Usage:
  python .claude/skills/listening-generate/scripts/build_listening.py \
      --data   scratch/data.js \
      --audio  "T1S1.m4a,T1S2.m4a,T1S3.m4a,T1S4.m4a" \
      --title  "Cambridge IELTS 20 — Listening Test 1" \
      --header "Cambridge IELTS 20 — Listening Test 1" \
      --badge  20 \
      --out    "listening/undone/cambridge/cambridge-20/Cambridge 20 Test 1 Listening.html" \
      [--map scratch/part2_map.png]      # embedded where the data.js has __MAPIMG__

The data.js must contain, between the DATA-START/DATA-END markers:
  const AUDIO = ["__AUDIO_0__","__AUDIO_1__","__AUDIO_2__","__AUDIO_3__"];
  const TEST = { sections:[...], groups:[...], transcript:{1:[...],2:[...],3:[...],4:[...]} };
  const EXPL = { "1":"...", ... };
  const answerHighlightQuotes = { "1":"exact transcript substring", ... };
"""
import argparse, base64, os, re, shutil, subprocess, sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--audio", required=True, help="comma-separated audio files, in Part 1-4 order")
    ap.add_argument("--title", required=True)
    ap.add_argument("--header", required=True)
    ap.add_argument("--badge", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--map", default=None, help="optional image embedded at __MAPIMG__")
    ap.add_argument("--template", default=os.path.join(REPO, "templates", "listening.html"))
    a = ap.parse_args()

    src = open(a.template, encoding="utf-8").read()
    data = open(a.data, encoding="utf-8").read()

    # identity
    src = re.sub(r"<title>[^<]*</title>", f"<title>{a.title}</title>", src, count=1)
    src = src.replace("IELTS Listening Test (template)", a.header)
    src = re.sub(r'(flex items-center justify-center">)IL(</div>)', rf"\g<1>{a.badge}\g<2>", src, count=1)

    # splice data
    pat = re.compile(r"/\* ==== DATA-START ==== \*/.*?/\* ==== DATA-END ==== \*/", re.S)
    if not pat.search(src): sys.exit("ERROR: DATA markers not found in template")
    src = pat.sub(lambda m: data.strip(), src, count=1)

    # optional map/diagram image
    if "__MAPIMG__" in src:
        if not a.map: sys.exit("ERROR: data.js uses __MAPIMG__ but no --map image was given")
        uri = "data:image/png;base64," + base64.b64encode(open(a.map, "rb").read()).decode()
        src = src.replace("__MAPIMG__", uri)

    # verify highlight quotes exist in the transcript text
    seg = data.split("answerHighlightQuotes")[1]
    qmap = dict(re.findall(r'"(\d+)":"([^"]*)"', seg))
    misses = [(q, v) for q, v in qmap.items() if v and not re.search(r"\s+".join(re.escape(t) for t in v.split()), data, re.I)]
    if misses:
        for q, v in misses: print(f"  QUOTE MISS Q{q}: {v!r}")
        sys.exit("ERROR: highlight quotes not found in transcript — trim to an exact substring")
    print(f"quotes verified: {sum(1 for v in qmap.values() if v)}")

    # copy the 4 tracks into the shared /audio/cambridge-<badge>/ folder and reference them by
    # path (so tests + /player.html share one copy; no giant embedded files, no 100 MB limit)
    files = [f.strip() for f in a.audio.split(",")]
    if len(files) != 4: sys.exit("ERROR: --audio must list exactly 4 files (Part 1-4)")
    tm = re.search(r"test[\s\-]*?(\d+)", os.path.basename(a.out), re.I)
    testno = tm.group(1) if tm else "x"
    adir = os.path.join(REPO, "audio", f"cambridge-{a.badge}")
    os.makedirs(adir, exist_ok=True)
    total = 0
    for i, f in enumerate(files):
        total += os.path.getsize(f)
        dest = f"test-{testno}-part-{i+1}.m4a"
        shutil.copyfile(f, os.path.join(adir, dest))
        tok = f"__AUDIO_{i}__"
        if tok not in src: sys.exit(f"ERROR: {tok} placeholder missing (data.js AUDIO array)")
        src = src.replace(tok, f"/audio/cambridge-{a.badge}/{dest}")
    print(f"audio -> /audio/cambridge-{a.badge}/ (4 tracks, {total/1e6:.1f} MB, referenced by path)")

    # id sanity
    ids = sorted(int(x) for x in re.findall(r"\bid:(\d+)", data))
    multi = re.findall(r"ids:\[([0-9,\s]+)\]", data)
    for grp in multi: ids += [int(x) for x in grp.split(",")]
    ids = sorted(set(ids))
    if ids != list(range(1, 41)):
        print(f"WARNING: question ids are not exactly 1..40 (got {len(ids)}: {ids[:5]}...{ids[-3:]})")

    # syntax check
    m = re.search(r"<script>\n(.*)</script>", src, re.S)
    chk = os.path.join(os.path.dirname(a.out) or ".", "_listen_check.js")
    open(chk, "w", encoding="utf-8").write(m.group(1))
    r = subprocess.run(["node", "--check", chk], capture_output=True, text=True)
    os.remove(chk)
    if r.returncode != 0: print(r.stderr); sys.exit("ERROR: script syntax check failed")
    print("node --check: OK")

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    open(a.out, "w", encoding="utf-8").write(src)
    print(f"WROTE {a.out}  ({len(src)/1e6:.1f} MB)")

if __name__ == "__main__":
    main()
